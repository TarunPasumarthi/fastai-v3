var el = x => document.getElementById(x);

function showPicker() {
  el("file-input").click();
}

function showPicked(input) {
  el("upload-label").innerHTML = input.files[0].name;
  var reader = new FileReader();
  reader.onload = function(e) {
    el("image-picked").src = e.target.result;
    el("image-picked").className = "";
  };
  reader.readAsDataURL(input.files[0]);
}

function analyze() {
  //var uploadFiles = el("file-input").files;
  var subhtml = document.getElementById("sub_cat");
  var subval = subhtml.options[subhtml.selectedIndex].value;
  var subreddit = subhtml.options[subhtml.selectedIndex].text;
  var mhtml = document.getElementById("model_cat");
  var mval = mhtml.options[mhtml.selectedIndex].value;
  var model = mhtml.options[mhtml.selectedIndex].text;
  var sentence=document.getElementById("senttext").value;
  if(subval===""){
    alert("Please pick a subreddit");
    return;
  }
  else if (mval===""){
    alert("Please pick a model");
    return;
  }
  else if (sentence===""){
    alert("Please enter a sentence");
    return;
  }

  el("analyze-button").innerHTML = "Generating...";
  var xhr = new XMLHttpRequest();
  var loc = window.location;
  xhr.open("POST", `${loc.protocol}//${loc.hostname}:${loc.port}/analyze`,
    true);
  xhr.onerror = function() {
    alert(xhr.responseText);
  };
  xhr.onload = function(e) {
    if (this.readyState === 4) {
      var response = JSON.parse(e.target.responseText);
      el("result-label").innerHTML = `${response["result"]}`;
    }
    el("analyze-button").innerHTML = "Generate";
  };

  var fileData = new FormData();
  fileData.append("subreddit", subreddit);
  fileData.append("model", model);
  fileData.append("sentence", sentence);
  xhr.send(fileData);
}

