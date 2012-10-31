from django import forms
from geodjango import settings
from countdracula.parsers.CountsWorkbookParser import CountsWorkbookParser
import logging
import os
import StringIO
import traceback


class TurnCountForm(forms.Form):

    sourcefile  = forms.FileField(max_length=150, help_text="Upload a count file to process.")
    xl_parser   = CountsWorkbookParser()
      
    def clean_sourcefile(self):
        """
        Make sure the sourcefile exists and that it's an xls file, and that the name indicates two streetnames.
        """        
        sourcefile_name = self.cleaned_data['sourcefile'].name
        
        # if not os.path.isabs(sourcefile_name):
        #     raise forms.ValidationError("Sourcefile must be an absolute path to an excel file.  Invalid value: %s" % sourcefile_name)
        
        # check if the file already exists in uploads
        if os.path.exists(os.path.join(settings.UPLOAD_DIR, sourcefile_name)):
            raise forms.ValidationError("Sourcefile %s already exists in uploads area." % sourcefile_name)
        
        if sourcefile_name[-4:].lower() != ".xls":
            raise forms.ValidationError("Sourcefile must be have a .xls suffix.  Invalid value: %s" % sourcefile_name)
        
        # set streetnames
        self.cleaned_data['streetnames'] = CountsWorkbookParser.parseFilename(sourcefile_name)

        if len(self.cleaned_data['streetnames']) != 2:
            raise forms.ValidationError("Sourcefile name should be of the format streetname1_streetname2.xls.  Invalid value: %s" % sourcefile_name)
        
        return self.cleaned_data['sourcefile']
        
    def read_sourcefile_and_insert_counts(self, request, file):
        """
        Do the work!  Read and insert the turn counts into the database.
        Returns ( num_processed, error_string ), where num_processed will be -1 on error.
        """
        
        # for now, save the file to c:\CountDracula\uploads
        with open(os.path.join(settings.UPLOAD_DIR, file.name), 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        
        # catch logs
        buffer      = StringIO.StringIO()
        logHandler  = logging.StreamHandler(buffer)
        logHandler.setLevel(logging.INFO)
        logging.getLogger().addHandler(logHandler)
        
        processed = self.xl_parser.readAndInsertTurnCounts(os.path.join(settings.UPLOAD_DIR, file.name), 
                                                           self.cleaned_data['streetnames'][0], 
                                                           self.cleaned_data['streetnames'][1], 
                                                           request.user,
                                                           logging.getLogger(''))       
        # stop catching logs
        logging.getLogger().removeHandler(logHandler)
        logHandler.flush()
        buffer.flush()
        
        return (processed, buffer.getvalue())
