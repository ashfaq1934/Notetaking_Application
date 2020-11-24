let accordionButton = document.querySelectorAll(".accordion-dropdown");
accordionButton.forEach(button => {
  button.addEventListener('click', function(){
    let section = this.parentElement;
    let panel = section.nextElementSibling;
    section.classList.toggle('active')
        if (panel.style.maxHeight) {
      panel.style.maxHeight = null;
      } else {
        panel.style.maxHeight = panel.scrollHeight + "px";
      }
  });
});

function validateForm() {
  let form = document.forms[0];
  let title = form.querySelector('input[name="title"]');
  let data = form.querySelector('textarea[name="editordata"]');
  let term = form.querySelector('textarea[name="term"]');
  let definition = form.querySelector('textarea[name="definition"]');

  if (title !== null){
    let check = checkForEvil(title.value);
    if (check === false){
      alert('Please remove JavaScript from input');
      event.preventDefault();
    }
  }
  if (data !== null){
    let check = checkForEvil(data.value);
    if (check === false){
      alert('Please remove JavaScript from input');
      event.preventDefault();
    }
  }
  if (term !== null){
    let check = checkForEvil(term.value);
    if (check === false){
      alert('Please remove JavaScript from input');
      event.preventDefault();
    }
  }
  if (definition !== null){
    let check = checkForEvil(definition.value);
    if (check === false){
      alert('Please remove JavaScript from input');
      event.preventDefault();
    }
  }
}

function checkForEvil(input) {
	if (input.indexOf("<script>") > -1) {
	  return false;
	}
	if (input.indexOf(":javascript") > -1) {
	  return false;
	}
	if (input.indexOf("javascript:") > -1) {
	  return false;
	}
	if (input.indexOf("function()") > -1) {
	  return false;
	}
}

