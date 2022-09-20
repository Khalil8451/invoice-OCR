import datetime

# from PyPDF2 import PdfFileReader, PdfFileWriter

ALLOWED_EXTENSIONS = set(['jpeg', 'zip', 'png', 'jpg', 'pdf'])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def create_date_dir():
    current_time = datetime.datetime.now()
    current_time = current_time.strftime("%d-%m-%Y, %H_%M_%S")

    return current_time

def must_include(required_fields, response):
    entered_fields = []
    success = True

    for s in response:
        entered_fields.append(s)

    for verify in required_fields:
        if verify not in entered_fields:
            success = False

    return success

# @staticmethod
# def pdf_splitter(pdf_to_split, saving_path):
#     inputpdf = PdfFileReader(pdf_to_split)
#     # open(pdf_to_split, "rb") this argument goes in the inputpdf parameters 
#     for i in range(inputpdf.numPages):
#         output = PdfFileWriter()
#         output.addPage(inputpdf.getPage(i))
#         save_path = saving_path + '/'
#         with open(save_path+"document-page%s.pdf" % i, "wb") as outputStream:
#             output.write(outputStream)
