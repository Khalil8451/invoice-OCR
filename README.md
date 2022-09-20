# invoice-OCR
A Flask application that would run on Windows server and user’s Bill and Receipts, which are either captured by camera or in form of an electronic file like pdf, jpg etc.

 * This app is based on yaml templates to extract the data from the invoices.
 * This app provides an API that helps you create custom templates for specific invoices.
  
1- All the invoices will be uploaded on server in a folder, zipfile etc... 

2- The uploaded invoices will be scanned by the OCR app and extract following information from the file and put them in a database table

  * amount
  * issuer
  * date_invoice
  * currency
  * invoice_number
