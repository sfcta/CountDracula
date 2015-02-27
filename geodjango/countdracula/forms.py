from django import forms
from geodjango import settings
from countdracula.parsers.CountsWorkbookParser import CountsWorkbookParser
import logging
import os
import StringIO
import traceback


class UploadCountForm(forms.Form):

    sourcefile  = forms.FileField(max_length=150, help_text="Upload a count file to process.")
    xl_parser   = CountsWorkbookParser()
      
    def clean_sourcefile(self):
        """
        Make sure the sourcefile exists and that it's an xls file, and that the name indicates two streetnames.
        """        
        sourcefile_name = self.cleaned_data['sourcefile'].name
        
        # if not os.path.isabs(sourcefile_name):
        #     raise forms.ValidationError("Sourcefile must be an absolute path to an excel file.  Invalid value: %s" % sourcefile_name)
        
       
        if sourcefile_name[-4:].lower() != ".xls" and sourcefile_name[-5:].lower() != ".xlsx":
            raise forms.ValidationError("Sourcefile must be have a .xls|.xlsx suffix.  Invalid value: %s" % sourcefile_name)
        
        # set streetnames
        self.cleaned_data['streetnames'] = CountsWorkbookParser.parseFilename(sourcefile_name)

        if len(self.cleaned_data['streetnames']) not in [2,3]:
            raise forms.ValidationError("Sourcefile name should be of the format streetname1_streetname2.xls or streetname_fromstreetname.tostreetname.xls.  Invalid value: %s" % sourcefile_name)
        
        return self.cleaned_data['sourcefile']
        
    def read_sourcefile_and_insert_counts(self, request, file):
        """
        Do the work!  Read and insert the turn counts into the database.
        Returns ( num_processed, error_string ), where num_processed will be -1 on error.
        """
        # Figure out a filename
        file_suffix_num     = 1
        new_filename        = file.name
        # check if the file already exists in uploads
        while os.path.exists(os.path.join(settings.UPLOAD_DIR, new_filename)):
            if file.name[-4:].lower() == ".xls":
                new_filename = "%s_%d%s" % (file.name[:-4],file_suffix_num,file.name[-4:])
            else:
                new_filename = "%s_%d%s" % (file.name[:-5],file_suffix_num,file.name[-5:])
            file_suffix_num += 1
 
        
        # for now, save the file to c:\CountDracula\uploads
        with open(os.path.join(settings.UPLOAD_DIR, new_filename), 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        
        # catch logs
        buffer      = StringIO.StringIO()
        logHandler  = logging.StreamHandler(buffer)
        logHandler.setLevel(logging.INFO)
        logging.getLogger().addHandler(logHandler)
        
        logging.info("Saving into uploads as [%s]" % new_filename)

        if len(self.cleaned_data['streetnames']) == 2:
            # turn counts
            processed = self.xl_parser.readAndInsertTurnCounts(os.path.join(settings.UPLOAD_DIR, new_filename), 
                                                               self.cleaned_data['streetnames'][0], 
                                                               self.cleaned_data['streetnames'][1], 
                                                               request.user,
                                                               logging.getLogger())
        else:
            # mainline counts
            processed = self.xl_parser.readAndInsertMainlineCounts(os.path.join(settings.UPLOAD_DIR, new_filename), 
                                                                   self.cleaned_data['streetnames'][0], 
                                                                   self.cleaned_data['streetnames'][1],
                                                                   self.cleaned_data['streetnames'][2],
                                                                   request.user, 
                                                                   logging.getLogger())  

        # stop catching logs
        logging.getLogger().removeHandler(logHandler)
        logHandler.flush()
        buffer.flush()
        return_str = buffer.getvalue()

        # remove file on failure
        if processed < 0:
            os.remove(os.path.join(settings.UPLOAD_DIR, new_filename))
            return_str += "Removed %s" % os.path.join(settings.UPLOAD_DIR,new_filename)

        return_str = return_str.replace("<","&lt;")
        return_str = return_str.replace(">","&gt;")
        return_str = return_str.replace("\n","<br />")
        return (processed, return_str)
