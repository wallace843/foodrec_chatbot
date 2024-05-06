async function getResponseBot(chatContent,bodyElement, text){
    const response = await fetch("/bot?" + new URLSearchParams({'text': text}));
    const js = await response.text()
    json = JSON.parse(js)
    bodyElement.innerHTML = json.response
    chatContent.scrollTop = chatContent.scrollHeight;
    document.getElementById("add_chat_btn").disabled = false;
  }

  // Create a new list item when clicking on the "Add" button
  function newElement() {
    document.getElementById("add_chat_btn").disabled = true;

    var inputUser = document.getElementById("input_user")
    var inputUserText = inputUser.value;
    inputUserText = inputUserText.trim()
    if(inputUserText === '') {
      alert("Digite algum texto!");
    }else{
      var chatContent = document.getElementById('chat-content')

      var divMediaContainer = document.createElement("div");
      var divMediaBody = document.createElement('div')
      var pTetx = document.createElement('p')
      var imgMedia = document.createElement('img')

      pTetx.innerHTML = inputUserText
      divMediaBody.appendChild(pTetx)

      divMediaBody.className = "media-body text-right align-self-center"
      divMediaContainer.appendChild(divMediaBody)
      
      imgMedia.src = "/static/images/user.png"
      imgMedia.alt = "Usuário"
      imgMedia.className = "align-self-center ml-3 rounded-circle"
      divMediaContainer.appendChild(imgMedia)
      
      divMediaContainer.className = 'media border p-3 mb-2 mt-0'
      chatContent.appendChild(divMediaContainer)

      chatContent.scrollTop = chatContent.scrollHeight;

      inputUser.value = ''

      divMediaContainer = document.createElement("div");
      divMediaBody = document.createElement('div')
      pTetx = document.createElement('p')
      imgMedia = document.createElement('img')

      imgMedia.src = "/static/images/dog_rob.png"
      imgMedia.alt = "Recbot"
      imgMedia.className = "align-self-center mr-3 rounded-circle"
      divMediaContainer.appendChild(imgMedia)

      divMediaBody.className = "media-body text-left text-white align-self-center"
      divMediaContainer.appendChild(divMediaBody)
      
      divMediaContainer.className = 'media bg-secondary border p-3 mb-2 mt-0'
      chatContent.appendChild(divMediaContainer)

      var span_spi = document.createElement('span')
      span_spi.className = 'spinner-border align-self-center'

      pTetx.appendChild(span_spi)

      getResponseBot(chatContent, pTetx, inputUserText)
      
      divMediaBody.appendChild(pTetx)

      chatContent.scrollTop = chatContent.scrollHeight;
    }
    inputUser.value = ''
  }

  const textInput = document.getElementById('input_user');
  textInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      if(!document.getElementById('add_chat_btn').disabled){
        newElement()
      }
    }
  });