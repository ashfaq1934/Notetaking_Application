let acc = document.getElementsByClassName("accordion");
let i;

for (i = 0; i < acc.length; i++) {
  acc[i].addEventListener("click", function() {
    this.classList.toggle("active");
    let panel = this.nextElementSibling;
    if (panel.style.maxHeight) {
      panel.style.maxHeight = null;
    } else {
      panel.style.maxHeight = panel.scrollHeight + "px";
    }
  });
}

function validateForm() {
  let form = document.forms[0];
  let title = form.querySelector('input[name="title"]');
  let data = form.querySelector('textarea[name="editordata"]');
  let term = form.querySelector('textarea[name="term"]');
  let definition = form.querySelector('textarea[name="definition"]');

  if (title !== null){
    let check = checkForEvil(title.value);
    if (check === false){
      alert('Booooooooo');
      event.preventDefault();
    }
  }
  if (data !== null){
    let check = checkForEvil(data.value);
    if (check === false){
      alert('Booooooooo');
      event.preventDefault();
    }
  }
  if (term !== null){
    let check = checkForEvil(term.value);
    if (check === false){
      alert('Booooooooo');
      event.preventDefault();
    }
  }
  if (definition !== null){
    let check = checkForEvil(definition.value);
    if (check === false){
      alert('Booooooooo');
      event.preventDefault();
    }
  }
}

function checkForEvil(carrier) {
	if (carrier.indexOf("<script>") > -1) { return false; }
	if (carrier.indexOf(":javascript") > -1) { return false; }
	if (carrier.indexOf("javascript:") > -1) { return false; }
	if (carrier.indexOf("function()") > -1) { return false; }
}

