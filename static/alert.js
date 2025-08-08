function closeAlert() {
  const ids = [
    "successClose", "senderDomestic", "senderExport", "ErrorData", "UpadteData",
    "Error", "DeteleData", "DeleteError", "SelectLine", "SelectLineUsers",
    "SendLine", "ServerError", "importExcel", "importExcelSuccess", "SendSuccess",
    "SendError", "deleteConfirm", "SendDeleteSuccess", "CustomerSuccess",
    "CustomerError", "deleteConfirmCustomer", "CustomerDeleteSuccess","ExcelError"
  ];

  ids.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.classList.remove("show");
  });
}
