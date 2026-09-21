// Opening a <dialog> as a modal is a method call, not an attribute, so it has to happen here.
// Worth the interop: showModal() gives focus trapping, Escape, the backdrop and returning focus
// to whatever opened it, all of which would otherwise be hand-written and half right.
window.livingdex = window.livingdex || {};

window.livingdex.openDialog = function (element) {
  if (element && !element.open) {
    element.showModal();
  }
};

window.livingdex.closeDialog = function (element) {
  if (element && element.open) {
    element.close();
  }
};
