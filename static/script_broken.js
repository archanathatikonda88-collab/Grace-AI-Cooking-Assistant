const chat = document.getElementById('chat');
const inputArea = document.getElementById('input-area');
const cardsDiv = document.getElementById('cards');
const recipeDetailView = document.getElementById('recipe-detail-view');
const backToCardsBtn = document.getElementById('back-to-cards');
// temporary element for the 'searching' indicator so we can remove it when results arrive
let currentSearchMsg = null;

// conversation state
const state = {
  ingredients: '',
  cuisine: '',
  diet: '',
  difficulty: '',
  taste: '',
  // Selection tracking to prevent duplicate prompts
  selectedCuisine: false,
  selectedDifficulty: false
};
document.addEventListener('DOMContentLoaded', () => {
  // Add back button functionality
  if (backToCardsBtn) {
    backToCardsBtn.addEventListener('click', () => {
      hideDetailView();
      showMainContent();
    });
  }
});

function appendMessage(who, text) {
  const m = document.createElement('div');
  m.className = 'message ' + who;
  m.innerText = text;
  chat.appendChild(m);
  chat.scrollTop = chat.scrollHeight;
  return m;
}

function appendMessageHtml(who, html) {
  const m = document.createElement('div');
  m.className = 'message ' + who;
  // Basic sanitation: disallow <script> tags by replacing them
  const safe = (html || '').replace(/<script[\s\S]*?>[\s\S]*?<\/script>/gi, '');
  m.innerHTML = safe;
  chat.appendChild(m);
  chat.scrollTop = chat.scrollHeight;
  return m;
}

function ensureInputVisible() {
  try {
    inputArea.scrollIntoView({behavior: 'smooth', block: 'center'});
  } catch (e) {
    // ignore
  }
}

// NOTE: we intentionally do not display user selections on the UI.
// Selected values are kept in `state` but not echoed back to avoid exposing them on the page.

function clearInputArea() { inputArea.innerHTML = ''; }

function disableButtonContainer(containerId) {
  const container = document.getElementById(containerId);
  if (container) {
    const buttons = container.querySelectorAll('button');
    buttons.forEach(btn => {
      btn.disabled = true;
      btn.style.opacity = '0.5';
      btn.style.cursor = 'not-allowed';
    });
  }
}

function resetConversation() {
  // Reset all state including selection flags
  Object.assign(state, {
    step: 'greeting',
    cuisine: '',
    diet: '',
    time: '',
    meal: '',
    ingredients: '',
    difficulty: '',
    selectedCuisine: false,
    selectedDifficulty: false
  });
  
  // Clear the chat, input area, and recipe cards
  chat.innerHTML = '';
  inputArea.innerHTML = '';
  cardsDiv.innerHTML = '';
  
  // Start fresh conversation with proper welcome message and input setup
  startConversation();
}

function startConversation() {
  appendMessage('bot', "Hi, I’m Grace. I’m here to help you make something delicious in the kitchen! What do you want to cook today?");
  // Clear any previously shown recipe cards when starting fresh
  cardsDiv.innerHTML = '';
  clearInputArea();
  
  // Start conversational flow
  setTimeout(() => {
    askForIngredients();
  }, 1000);
}

function showTextInput(field, placeholder) {
  clearInputArea();
  const input = document.createElement('input');
  input.type = 'text';
  input.placeholder = placeholder;
  input.className = 'text-input';
  const btn = document.createElement('button');
  btn.type = 'button';
  btn.innerText = 'Next';
  btn.addEventListener('click', () => {
  const val = input.value.trim();
  console.debug('Next clicked', {field, val});
  if (!val) return;
  state[field] = val;
    proceedConversation(field);
  });
  inputArea.appendChild(input);
  inputArea.appendChild(btn);
  input.focus();
  ensureInputVisible();
}





function showChoiceInput(field, label, options) {
  // Render options inline below the last bot message for a tighter UX
  clearInputArea();
  const lastBot = Array.from(chat.querySelectorAll('.message.bot')).pop();
  const container = document.createElement('div');
  container.className = 'inline-choices';
      
      if (event.results[i].isFinal) {
        finalTranscript += transcript;
      } else {
        interimTranscript += transcript;
      }
    }
    
    // Show live preview in input box
    const displayText = finalTranscript + interimTranscript;
    if (inputEl) {
      inputEl.value = displayText;
      inputEl.style.backgroundColor = '#f0fff0'; // Light green background while listening
    }
    
    console.log('Voice input (interim):', displayText);
  };
  
  recog.onerror = (event) => {
    console.error('Speech recognition error:', event.error);
    setMicState(false);
    handleSpeechError(event.error);
  };
  
  recog.onend = () => {
    setMicState(false);
    
    if (inputEl) {
      inputEl.style.backgroundColor = ''; // Reset background
    }
    
    if (finalTranscript.trim()) {
      const rawText = finalTranscript.trim();
      
      // First, try to process as button selection if we're on ingredients
      let handledAsButton = false;
      if (field === 'ingredients' || !field) {
        handledAsButton = processVoiceButtonSelection(rawText);
      }
      
      // If not handled as button selection, process as text input
      if (!handledAsButton) {
        const processedText = processVoiceInput(rawText, field);
        
        if (inputEl) {
          inputEl.value = processedText;
        }
        
        // Store the recognized text
        state[field] = processedText;
        
        showVoiceMessage(`✅ Got it: "${processedText}"`);
        
        // Auto-advance if this is an ingredient input
        if (field === 'ingredients' && processedText) {
          setTimeout(() => {
            proceedConversation(field);
          }, 1000);
        }
      }
    } else {
      showVoiceMessage('❌ No speech detected. Please try again.');
    }
  };
  
  recog.onstart = () => {
    console.log('Speech recognition started');
  };
  
  try {
    recog.start();
  } catch (error) {
    console.error('Failed to start speech recognition:', error);
    setMicState(false);
    showVoiceMessage('Failed to start voice recognition. Please try again.');
  }
}

// Enhanced microphone state management with better visual feedback
function setMicState(isListening) {
  const micButtons = document.querySelectorAll('.mic-button');
  const voiceToggle = document.getElementById('voice-toggle');
  
  micButtons.forEach(button => {
    if (isListening) {
      button.style.opacity = '1';
      button.style.transform = 'scale(1.1)';
      button.style.backgroundColor = '#ff4444';
      button.style.color = 'white';
      button.style.animation = 'pulse 1s infinite';
      button.innerText = '🔴'; // Recording indicator
      button.title = 'Recording... Click to stop';
    } else {
      button.style.opacity = '0.9';
      button.style.transform = 'none';
      button.style.backgroundColor = '';
      button.style.color = '';
      button.style.animation = '';
      button.innerText = '🎤';
      button.title = 'Voice input';
    }
  });
  
  // Also update main voice toggle for visual consistency
  if (voiceToggle && isListening) {
    voiceToggle.style.animation = 'pulse 1s infinite';
    voiceToggle.style.backgroundColor = '#ff4444';
  } else if (voiceToggle) {
    voiceToggle.style.animation = '';
    voiceToggle.style.backgroundColor = '';
  }
}

// Legacy function for compatibility
function micState(on) {
  setMicState(on);
}

// Show voice-related messages to users
function showVoiceMessage(message) {
  const existingMsg = document.querySelector('.voice-feedback-message');
  if (existingMsg) {
    existingMsg.remove();
  }
  
  const messageEl = document.createElement('div');
  messageEl.className = 'message bot voice-feedback-message';
  messageEl.innerHTML = `<span class="voice-icon">🎙️</span> ${message}`;
  messageEl.style.backgroundColor = '#e8f5e8';
  messageEl.style.border = '1px solid #4CAF50';
  messageEl.style.borderRadius = '8px';
  messageEl.style.padding = '8px 12px';
  messageEl.style.margin = '5px 0';
  messageEl.style.fontSize = '14px';
  
  chat.appendChild(messageEl);
  chat.scrollTop = chat.scrollHeight;
  
  // Auto-remove after 4 seconds
  setTimeout(() => {
    if (messageEl && messageEl.parentNode) {
      messageEl.remove();
    }
  }, 4000);
}

// Handle microphone permission errors
function handleMicrophoneError(error) {
  console.error('Microphone access error:', error);
  let message = '';
  
  switch (error.name) {
    case 'NotAllowedError':
      message = '🚫 Microphone access denied. Please allow microphone access and try again.';
      break;
    case 'NotFoundError':
      message = '🎤 No microphone found. Please connect a microphone and try again.';
      break;
    case 'NotSupportedError':
      message = '❌ Microphone not supported in this browser. Try Chrome or Edge.';
      break;
    default:
      message = `⚠️ Microphone error: ${error.message || 'Unknown error'}`;
  }
  
  showVoiceMessage(message);
}

// Handle speech recognition errors
function handleSpeechError(errorType) {
  let message = '';
  
  switch (errorType) {
    case 'no-speech':
      message = '🤐 No speech detected. Please try speaking again.';
      break;
    case 'audio-capture':
      message = '🎤 Audio capture failed. Check your microphone.';
      break;
    case 'not-allowed':
      message = '🚫 Speech recognition not allowed. Check browser permissions.';
      break;
    case 'network':
      message = '🌐 Network error. Check your internet connection.';
      break;
    case 'aborted':
      message = '⏹️ Speech recognition was stopped.';
      break;
    default:
      message = `⚠️ Speech recognition error: ${errorType}`;
  }
  
  showVoiceMessage(message);
}

// Process and clean up voice input
function processVoiceInput(rawText, field) {
  let processedText = rawText.toLowerCase().trim();
  
  // If this is ingredient input, try to map spoken ingredients to available options
  if (field === 'ingredients') {
    processedText = mapSpokenIngredients(processedText);
  }
  
  // Clean up common speech-to-text issues
  processedText = processedText
    .replace(/\bcomma\b/gi, ',')           // "chicken comma rice" → "chicken, rice"
    .replace(/\band\b/gi, ',')            // "chicken and rice" → "chicken, rice"  
    .replace(/\s+,/g, ',')                // Clean up spaces before commas
    .replace(/,\s+/g, ', ')               // Normalize comma spacing
    .replace(/^,+|,+$/g, '')              // Remove leading/trailing commas
    .replace(/,{2,}/g, ',')               // Remove multiple consecutive commas
    .trim();
  
  return processedText;
}

// Map spoken ingredient names to available options
function mapSpokenIngredients(spokenText) {
  const ingredientMappings = {
    // Common ingredient mappings
    'tomatoes': 'tomato',
    'potatoes': 'potato', 
    'onions': 'onion',
    'peppers': 'pepper',
    'carrots': 'carrot',
    'mushrooms': 'mushroom',
    
    // Protein mappings
    'chickens': 'chicken',
    'beef': 'beef',
    'pork': 'pork',
    'fish': 'fish',
    'eggs': 'egg',
    'egg': 'egg',
    
    // Grain mappings
    'rice': 'rice',
    'pasta': 'pasta',
    'noodles': 'pasta',
    'bread': 'bread',
    
    // Spelling variations
    'tommato': 'tomato',
    'tomatoe': 'tomato',
    'potatoe': 'potato',
    'onoin': 'onion',
  };
  
  // Process each word and map known ingredients
  let words = spokenText.split(/[,\s]+/);
  let mappedWords = words.map(word => {
    const cleaned = word.toLowerCase().trim();
    return ingredientMappings[cleaned] || cleaned;
  });
  
  // Remove empty words and join
  return mappedWords.filter(word => word.length > 0).join(', ');
}

// Voice button selection - trigger ingredient buttons by voice
function processVoiceButtonSelection(spokenText) {
  const text = spokenText.toLowerCase().trim();
  
  // Get all available ingredient buttons
  const ingredientButtons = document.querySelectorAll('.ingredient-button');
  const buttonMappings = new Map();
  
  // Map button text to buttons for easy lookup
  ingredientButtons.forEach(button => {
    const buttonText = button.textContent.toLowerCase().trim();
    buttonMappings.set(buttonText, button);
    
    // Also map plural forms
    if (buttonText.endsWith('s') === false) {
      buttonMappings.set(buttonText + 's', button);
    }
    if (buttonText.endsWith('s')) {
      buttonMappings.set(buttonText.slice(0, -1), button);
    }
  });
  
  // Check if user said a recognizable ingredient name
  const words = text.split(/[,\s]+/);
  let triggeredButtons = [];
  
  words.forEach(word => {
    const cleanWord = word.trim();
    if (buttonMappings.has(cleanWord)) {
      const button = buttonMappings.get(cleanWord);
      if (button && !button.classList.contains('selected')) {
        button.click(); // Trigger the button
        triggeredButtons.push(button.textContent.trim());
      }
    }
  });
  
  // Provide feedback if buttons were triggered
  if (triggeredButtons.length > 0) {
    const buttonList = triggeredButtons.join(', ');
    showVoiceMessage(`✅ Selected ingredients: ${buttonList}`);
    return true; // Successfully processed as button selection
  }
  
  // Check for common voice commands
  if (text.includes('select') || text.includes('choose') || text.includes('add')) {
    // Extract ingredient names after command words
    const commandWords = ['select', 'choose', 'add', 'pick'];
    let ingredientPart = text;
    
    commandWords.forEach(cmd => {
      if (text.includes(cmd)) {
        const parts = text.split(cmd);
        if (parts.length > 1) {
          ingredientPart = parts[1].trim();
        }
      }
    });
    
    // Try to match ingredients in the command
    const ingredientWords = ingredientPart.split(/[,\s]+/);
    let selectedIngredients = [];
    
    ingredientWords.forEach(word => {
      const cleanWord = word.trim();
      if (buttonMappings.has(cleanWord)) {
        const button = buttonMappings.get(cleanWord);
        if (button && !button.classList.contains('selected')) {
          button.click();
          selectedIngredients.push(button.textContent.trim());
        }
      }
    });
    
    if (selectedIngredients.length > 0) {
      showVoiceMessage(`✅ Added: ${selectedIngredients.join(', ')}`);
      return true;
    } else {
      showVoiceMessage(`❓ I couldn't find those ingredients. Try saying ingredient names like "chicken" or "rice".`);
      return true;
    }
  }
  
  return false; // Not processed as button selection
}

function showChoiceInput(field, label, options) {
  // Render options inline below the last bot message for a tighter UX
  clearInputArea();
  const lastBot = Array.from(chat.querySelectorAll('.message.bot')).pop();
  const container = document.createElement('div');
  container.className = 'inline-choices';
  if (field === 'difficulty') {
    container.id = 'difficulty-choices'; // Add ID for difficulty buttons
  }
  options.forEach(opt => {
    const b = document.createElement('button');
    b.type = 'button';
    b.innerText = opt;
    b.addEventListener('click', () => {
      // Check if this is a difficulty selection and already selected
      if (field === 'difficulty' && state.selectedDifficulty) return;
      
      if (field === 'time') state[field] = String(opt); else state[field] = opt;
      
      // Mark difficulty as selected if this is difficulty field
      if (field === 'difficulty') {
        state.selectedDifficulty = true;
        disableButtonContainer('difficulty-choices');
        
        // Show loading animation for difficulty selection
        showLoadingAnimation();
        
        // Hide loading animation after 2.5 seconds and proceed
        setTimeout(() => {
          hideLoadingAnimation();
          proceedConversation(field);
        }, 2500);
        
        return; // Don't proceed immediately for difficulty
      }
      
      proceedConversation(field);
    });
    container.appendChild(b);
  });
  if (lastBot) {
    // insert choices right after the last bot message
    lastBot.insertAdjacentElement('afterend', container);
  } else {
    inputArea.appendChild(container);
  }
  ensureInputVisible();
}

function showCuisineChoices(){
  appendMessage('bot', 'Which cuisine would you prefer?');
  clearInputArea();
  const choices = ['Indian','Italian','Chinese','Mediterranean','Mexican'];
  const container = document.createElement('div');
  container.className = 'inline-choices';
  container.id = 'cuisine-choices'; // Add ID for easy targeting
  // create quick-pick buttons for common cuisines
  choices.forEach(c => {
    const b = document.createElement('button');
    b.type = 'button';
    b.innerText = c;
    b.addEventListener('click', () => {
      if (state.selectedCuisine) return; // Prevent multiple selections
      state['cuisine'] = c;
      state.selectedCuisine = true;
      // Disable all cuisine buttons
      disableButtonContainer('cuisine-choices');
      recipeProceed('cuisine');
    });
    container.appendChild(b);
  });
  // 'Other' reveals a text input for custom cuisine
  const other = document.createElement('button');
  other.type = 'button';
  other.innerText = 'Other';
  other.addEventListener('click', () => {
    if (state.selectedCuisine) return; // Prevent multiple selections
    // show text input inline and allow Enter to submit
    clearInputArea();
    appendMessage('bot', 'Please type the cuisine you prefer (e.g., Moroccan, Thai, African)');
    clearInputArea();
    const input = document.createElement('input');
    input.type = 'text';
    input.placeholder = 'Type cuisine (e.g., Moroccan)';
    input.className = 'text-input';
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.innerText = 'Select';
    const submitCuisine = () => {
      const v = input.value.trim();
      if (!v) return;
      state['cuisine'] = v;
      state.selectedCuisine = true;
      // Disable all cuisine buttons
      disableButtonContainer('cuisine-choices');
      recipeProceed('cuisine');
    };
    btn.addEventListener('click', submitCuisine);
    // submit on Enter
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        submitCuisine();
      }
    });
    // place the input inline under the bot message
    const lastBot = Array.from(chat.querySelectorAll('.message.bot')).pop();
    const wrap = document.createElement('div');
    wrap.className = 'inline-choices';
    wrap.appendChild(input);
    wrap.appendChild(btn);
    if (lastBot) lastBot.insertAdjacentElement('afterend', wrap); else inputArea.appendChild(wrap);
    input.focus();
  });
  container.appendChild(other);
  const lastBot = Array.from(chat.querySelectorAll('.message.bot')).pop();
  if (lastBot) lastBot.insertAdjacentElement('afterend', container); else inputArea.appendChild(container);
  ensureInputVisible();
  }

function recipeProceed(lastField) {
  console.debug('recipeProceed called', {lastField, state});
  switch(lastField) {
    case 'ingredients':
      // ask cuisine only if not already selected
      if (!state.selectedCuisine) {
        showCuisineChoices();
      } else {
        // if cuisine already selected, proceed to difficulty
        recipeProceed('cuisine');
      }
      break;
    case 'cuisine':
      // skip diet and meal prompts — proceed to difficulty directly
      // only ask difficulty if not already selected
      if (!state.selectedDifficulty) {
        appendMessage('bot', 'Would you like an easy, moderate, or complex recipe?');
        showChoiceInput('difficulty', '', ['easy', 'moderate', 'complex']);
      } else {
        // if difficulty already selected, proceed to fetch suggestions
        recipeProceed('difficulty');
      }
      break;
    case 'difficulty':
      // inputs collected — fetch suggestions
      clearInputArea();
      fetchSuggestions();
      break;
    default:
      console.log('Unknown field:', lastField);
  }
}

function showInitialRecipePreviews(){
  // function removed; initial previews disabled
}

async function generateRecipes() {
  // This function is now deprecated in favor of fetchSuggestions() 
  // which has improved timing and animation flow.
  // Redirect to the new improved function
  return fetchSuggestions();
}

function showNoRecipesOptions() {
  clearInputArea();
  
  const container = document.createElement('div');
  container.className = 'chat-buttons-container';
  
  const options = [
    { text: 'Try different ingredients', action: () => askForIngredients() },
    { text: 'Change cuisine type', action: () => askForCuisine() },
    { text: 'Start over', action: () => resetConversation() }
  ];
  
  options.forEach((option, index) => {
    const btn = document.createElement('button');
    btn.innerText = option.text;
    btn.className = 'chat-choice-btn';
    btn.onclick = option.action;
    
    // Staggered animation
    btn.style.opacity = '0';
    btn.style.transform = 'translateY(20px)';
    setTimeout(() => {
      btn.style.transition = 'all 0.3s ease';
      btn.style.opacity = '1';
      btn.style.transform = 'translateY(0)';
    }, index * 150);
    
    container.appendChild(btn);
  });
  
  inputArea.appendChild(container);
}

function showErrorOptions() {
  clearInputArea();
  
  const container = document.createElement('div');
  container.className = 'chat-buttons-container';
  
  const retryBtn = document.createElement('button');
  retryBtn.innerText = 'Try again';
  retryBtn.className = 'chat-choice-btn';
  retryBtn.onclick = () => generateRecipes();
  
  const startOverBtn = document.createElement('button');
  startOverBtn.innerText = 'Start over';
  startOverBtn.className = 'chat-choice-btn';
  startOverBtn.onclick = () => resetConversation();
  
  // Add fade-in animation
  [retryBtn, startOverBtn].forEach((btn, index) => {
    btn.style.opacity = '0';
    btn.style.transform = 'translateY(20px)';
    setTimeout(() => {
      btn.style.transition = 'all 0.3s ease';
      btn.style.opacity = '1';
      btn.style.transform = 'translateY(0)';
    }, index * 150);
    
    container.appendChild(btn);
  });
  
  inputArea.appendChild(container);
}

async function fetchSuggestions() {
  // Step 1: Immediately show Grace's cooking animation (no text message yet)
  showLoadingAnimation();
  
  // Clear previously shown cards while searching
  cardsDiv.innerHTML = '';
  clearInputArea();

  try {
    // Step 2: Make API call while animation is visible
    const res = await fetch('/api/recipes', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        ingredients: state.ingredients,
        cuisine: state.cuisine,
        diet: state.diet,
        difficulty: state.difficulty,
        meal: state.meal,
        broaden: state.broaden
      })
    });
    
    const data = await res.json();
    
    // Step 3: Hide animation first
    hideLoadingAnimation();
    
    // Step 4: Show brief "Perfect! Let me find..." message (only after animation is hidden)
    const preparingMsg = appendMessage('bot', 'Perfect! Let me find some amazing recipes for you... 🍳 Grace is finding recipes for you...');
    
    // Brief delay to let users read the message
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // Remove the preparing message before showing results
    if (preparingMsg && preparingMsg.parentNode) {
      preparingMsg.parentNode.removeChild(preparingMsg);
    }
    
    // Clear broaden flag after a single request
    if (state['broaden']) delete state['broaden'];
    
    // Step 5: Show results or no-results options
    if (!data.cards || data.cards.length === 0) {
      // no matches — show a concise message and the broaden/start over choices
      appendMessage('bot', "I couldn't find recipes that match those ingredients and filters.");
      clearInputArea();
      const container = document.createElement('div');
      container.className = 'choices';
      const b1 = document.createElement('button');
      b1.type = 'button';
      b1.innerText = 'Broaden ingredients';
      b1.addEventListener('click', () => {
        // set broaden flag so backend relaxes matching for the next fetch, then re-ask ingredients
        state['broaden'] = true;
        showTextInput('ingredients', 'Enter more or fewer ingredients (comma separated)');
      });
      const b2 = document.createElement('button');
      b2.type = 'button';
      b2.innerText = 'Start over';
      b2.addEventListener('click', () => {
        resetConversation();
      });
      container.appendChild(b1);
      container.appendChild(b2);
      inputArea.appendChild(container);
    } else {
      showRecipeCards(data.cards);
    }
    
  } catch (error) {
    // Handle any errors during the fetch process
    console.error('Error fetching recipes:', error);
    hideLoadingAnimation();
    appendMessage('bot', 'Sorry, there was an error getting recipes. Please try again.');
    
    // Show start over option
    clearInputArea();
    const container = document.createElement('div');
    container.className = 'choices';
    const restartBtn = document.createElement('button');
    restartBtn.type = 'button';
    restartBtn.innerText = 'Start over';
    restartBtn.addEventListener('click', () => {
      resetConversation();
    });
    container.appendChild(restartBtn);
    inputArea.appendChild(container);
  }
}

function showRecipeCards(cards) {
  // display recipe cards with smooth animations
  cardsDiv.innerHTML = '';
  cardsDiv.style.display = 'flex';
  
  // ensure external image URLs are cached first
  const cachePromises = cards.map(async (c) => {
    if (c.image && (c.image.startsWith('http://') || c.image.startsWith('https://'))) {
      try {
        const r = await fetch('/api/cache-image', {
          method: 'POST', 
          headers: {'Content-Type': 'application/json'}, 
          body: JSON.stringify({url: c.image, name: c.name, cuisine: state.cuisine})
        });
        const j = await r.json();
        if (j.local) c.image = j.local;
      } catch (err) {
        console.warn('Error caching image:', err);
      }
    }
  });
  
  // Wait for all images to be cached, then display cards
  Promise.all(cachePromises).then(() => {
    cards.forEach((c, index) => {
      const card = document.createElement('div');
      card.className = 'recipe-card';
      
      // Add initial state for animation
      card.style.opacity = '0';
      card.style.transform = 'translateY(30px) scale(0.95)';
      
      // Create card content
      const img = document.createElement('img');
      img.src = c.image || '/static/images/spaghetti.jpg';
      img.alt = c.name;
      img.className = 'recipe-image';
      img.onerror = function() {
        this.onerror = null; // Prevent infinite loop
        this.src = '/static/images/spaghetti.jpg';
      };
      
      const content = document.createElement('div');
      content.className = 'recipe-content';
      
      const title = document.createElement('h3');
      title.className = 'recipe-title';
      title.textContent = c.name;
      
      const description = document.createElement('p');
      description.className = 'recipe-description';
      description.textContent = c.short || 'Delicious recipe waiting for you to try!';
      
      content.appendChild(title);
      content.appendChild(description);
      card.appendChild(img);
      card.appendChild(content);
      
      // Add click handler
      card.onclick = () => showRecipeDetail(c);
      
      cardsDiv.appendChild(card);
      
      // Staggered fade-in animation
      setTimeout(() => {
        card.style.transition = 'all 0.4s ease';
        card.style.opacity = '1';
        card.style.transform = 'translateY(0) scale(1)';
      }, index * 150);
    });
  }).catch(err => {
    console.error('Error displaying recipe cards:', err);
    // Fallback: show cards without caching
    cards.forEach((c, index) => {
      const card = document.createElement('div');
      card.className = 'recipe-card';
      card.style.opacity = '0';
      card.style.transform = 'translateY(30px)';
      
      const img = document.createElement('img');
      img.src = c.image || '/static/images/spaghetti.jpg';
      img.alt = c.name;
      img.className = 'recipe-image';
      img.onerror = function() {
        this.onerror = null; // Prevent infinite loop
        this.src = '/static/images/spaghetti.jpg';
      };
      
      const content = document.createElement('div');
      content.className = 'recipe-content';
      
      const title = document.createElement('h3');
      title.className = 'recipe-title';
      title.textContent = c.name;
      
      const description = document.createElement('p');
      description.className = 'recipe-description';
      description.textContent = c.short || 'Delicious recipe waiting for you to try!';
      
      content.appendChild(title);
      content.appendChild(description);
      card.appendChild(img);
      card.appendChild(content);
      card.onclick = () => showRecipeDetail(c);
      
      cardsDiv.appendChild(card);
      
      setTimeout(() => {
        card.style.transition = 'all 0.4s ease';
        card.style.opacity = '1';
        card.style.transform = 'translateY(0)';
      }, index * 150);
    });
  });
}

async function showRecipeDetail(recipe) {
  // Show the detail view and hide the main content
  hideMainContent();
  showDetailView();
  
  // Clear previous content and show loading state
  clearDetailContent();
  
  // If we receive a recipe object directly, use it immediately
  if (typeof recipe === 'object' && recipe.name) {
    populateDetailView(recipe);
    return;
  }
  
  // Otherwise, treat it as an ID and fetch from API (fallback)
  showDetailLoading();
  
  try {
    const res = await fetch(`/api/recipe/${recipe}`);
    const recipeData = await res.json();
    
    // Hide loading and populate the detail view
    hideDetailLoading();
    populateDetailView(recipeData);
    
  } catch (err) {
    console.error('Failed to fetch recipe detail', err);
    hideDetailLoading();
    showDetailError();
  }
}

function hideMainContent() {
  chat.style.display = 'none';
  inputArea.style.display = 'none';
  cardsDiv.style.display = 'none';
}

function showMainContent() {
  chat.style.display = 'block';
  inputArea.style.display = 'flex';
  cardsDiv.style.display = 'flex';
  
  // Hide feedback section when returning to main content
  const feedbackSection = document.querySelector('.feedback-section');
  if (feedbackSection) {
    feedbackSection.classList.remove('visible');
  }
}

function showDetailView() {
  recipeDetailView.style.display = 'block';
}

function hideDetailView() {
  recipeDetailView.style.display = 'none';
}

function clearDetailContent() {
  document.getElementById('detail-image').src = '';
  document.getElementById('detail-title').textContent = '';
  document.getElementById('detail-description').textContent = '';
  document.getElementById('ingredients-list').innerHTML = '';
  document.getElementById('instructions-list').innerHTML = '';
  document.getElementById('expand-recipe-btn').style.display = 'none';
}

function showDetailLoading() {
  document.getElementById('detail-title').textContent = 'Loading recipe...';
  document.getElementById('detail-description').textContent = 'Please wait while we fetch the recipe details.';
}

function hideDetailLoading() {
  // Loading content will be replaced by actual content
}

function showDetailError() {
  document.getElementById('detail-title').textContent = 'Error Loading Recipe';
  document.getElementById('detail-description').textContent = 'Sorry, we couldn\'t load this recipe. Please try again.';
}

function populateDetailView(recipe) {
  // Handle image display only
  const detailImage = document.getElementById('detail-image');
  
  // Set recipe image with fallback
  detailImage.alt = recipe.name;
  
  // Handle image loading with error fallback
  if (recipe.image && recipe.image.trim() !== '') {
    detailImage.src = recipe.image;
    detailImage.onerror = function() {
      this.onerror = null; // Prevent infinite loop
      this.src = '/static/images/quinoa_salad.jpg';
    };
  } else {
    detailImage.src = '/static/images/quinoa_salad.jpg';
  }
  
  document.getElementById('detail-title').textContent = recipe.name;
  document.getElementById('detail-description').textContent = recipe.short || '';
  
  // Show basic ingredients if available
  const ingredientsList = document.getElementById('ingredients-list');
  if (recipe.ingredients && recipe.ingredients.length > 0) {
    ingredientsList.innerHTML = recipe.ingredients.map(ing => `<li>${ing}</li>`).join('');
  } else {
    ingredientsList.innerHTML = '<li>Ingredients will be shown when you expand the full recipe.</li>';
  }
  
  // Show basic instructions if available  
  const instructionsList = document.getElementById('instructions-list');
  if (recipe.instructions && recipe.instructions.length > 0) {
    // Clean up instructions and remove duplicate numbering
    const cleanedInstructions = recipe.instructions.map(inst => {
      if (typeof inst === 'string') {
        return inst.replace(/^\d+\.\s*/, '').trim();
      }
      return inst;
    });
    instructionsList.innerHTML = cleanedInstructions.map(inst => `<li>${inst}</li>`).join('');
  } else {
    instructionsList.innerHTML = '<li>Click "View full recipe" below to see detailed instructions.</li>';
  }
  
  // Show expand button if recipe is not fully expanded or if we only have basic data
  if (!recipe.expanded || !recipe.instructions || recipe.instructions.length === 0) {
    const expandBtn = document.getElementById('expand-recipe-btn');
    expandBtn.style.display = 'block';
    expandBtn.onclick = () => expandRecipeInDetail(recipe.id);
  } else {
    // Hide expand button if we already have full data
    const expandBtn = document.getElementById('expand-recipe-btn');
    expandBtn.style.display = 'none';
  }
  
  // Reset and initialize feedback section for new recipe
  resetFeedbackSection();
  initializeFeedbackSection();
}

async function expandRecipeInDetail(recipeId) {
  const expandBtn = document.getElementById('expand-recipe-btn');
  const originalText = expandBtn.textContent;
  
  expandBtn.textContent = 'Loading...';
  expandBtn.disabled = true;
  
  try {
    const res = await fetch('/api/expand-recipe', {
      method: 'POST', 
      headers: {'Content-Type':'application/json'}, 
      body: JSON.stringify({id: recipeId})
    });
    const data = await res.json();
    
    if (res.ok && data.expanded) {
      // Update the detail view with expanded content
      updateDetailWithExpanded(data.expanded);
      expandBtn.style.display = 'none';
    } else {
      expandBtn.textContent = 'Failed - try again';
      expandBtn.disabled = false;
    }
  } catch (err) {
    console.error('Failed to expand recipe', err);
    expandBtn.textContent = 'Error - try again';
    expandBtn.disabled = false;
  }
}

function updateDetailWithExpanded(expanded) {
  // Update ingredients with detailed versions
  if (expanded.ingredients_detailed && expanded.ingredients_detailed.length > 0) {
    const ingredientsList = document.getElementById('ingredients-list');
    ingredientsList.innerHTML = expanded.ingredients_detailed.map(ing => `<li>${ing}</li>`).join('');
  }
  
  // Update instructions with detailed versions
  if (expanded.instructions_detailed && expanded.instructions_detailed.length > 0) {
    const instructionsList = document.getElementById('instructions-list');
    // Clean instruction text to remove duplicate numbering
    const cleanedInstructions = expanded.instructions_detailed.map(step => {
      return step.replace(/^\d+\.\s*/, '').trim();
    });
    instructionsList.innerHTML = cleanedInstructions.map(inst => `<li>${inst}</li>`).join('');
  }
}

function renderExpanded(recipe, expanded) {
  // Build an HTML snippet and append it into the existing recipe-detail message if present
  let html = '';
  if (expanded.ingredients_detailed) {
    html += '<h4>Ingredients (detailed)</h4>';
    html += '<ul>' + expanded.ingredients_detailed.map(it => `<li>${it}</li>`).join('') + '</ul>';
  }
  if (expanded.instructions_detailed) {
    html += '<h4>Instructions (detailed)</h4>';
    // Strip leading numbers and periods from instruction text to avoid duplicate numbering
    const cleanedInstructions = expanded.instructions_detailed.map(step => {
      // Remove leading digits followed by period and optional space (e.g., "1. " or "2.")
      return step.replace(/^\d+\.\s*/, '').trim();
    });
    html += '<ol>' + cleanedInstructions.map(step => `<li>${step}</li>`).join('') + '</ol>';
  }
  if (!html) return;
  // try to find the most recent recipe-detail container in the chat
  const container = Array.from(chat.querySelectorAll('.message.bot .recipe-detail')).pop();
  if (container) {
    // append expanded details inside the existing container
    const wrapper = document.createElement('div');
    wrapper.innerHTML = html;
    container.appendChild(wrapper);
  } else {
    // fallback: append as a new bot message
    appendMessageHtml('bot', html);
  }
}

// when feedback submitted, thank user
// override proceedConversation to handle feedback field
const originalProceed = recipeProceed.bind(this);
function proceedConversation(lastField) {
  console.debug('overridden proceedConversation', {lastField, state});
  if (lastField === 'feedback') {
    const fb = (state['feedback'] || '').trim();
    // if user typed 'okay' or similar, ask for explicit final feedback
    if (['okay', 'ok', 'fine', 'yes'].includes(fb.toLowerCase())) {
      appendMessage('bot', 'Thank you! Please give me feedback on what needs to be improved.');
      clearInputArea();
      showTextInput('final_feedback', 'Type feedback about what to improve');
      return;
    }
    // otherwise treat as actual feedback and save
    appendMessage('bot', 'Thanks — sending your feedback to Grace...');
    clearInputArea();
    try {
      fetch('/api/feedback', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({feedback: fb, context: state})
      }).then(r => {
        appendMessage('bot', 'Thank you! Your feedback was saved.');
        const btn = document.createElement('button');
        btn.innerText = 'Start Over';
        btn.onclick = () => resetConversation();
        inputArea.appendChild(btn);
      }).catch(e => {
        appendMessage('bot', 'Sorry, I could not save your feedback.');
        const btn = document.createElement('button');
        btn.innerText = 'Start Over';
        btn.onclick = () => resetConversation();
        inputArea.appendChild(btn);
      });
    } catch (e) {
      appendMessage('bot', 'Sorry, I could not save your feedback.');
    }
    return;
  }

  if (lastField === 'final_feedback') {
    const fb2 = (state['final_feedback'] || '').trim();
    appendMessage('bot', 'Thanks — sending your final feedback to Grace...');
    clearInputArea();
    try {
      fetch('/api/feedback', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({feedback: fb2, context: state, final: true})
      }).then(r => {
        appendMessage('bot', 'Thank you! Your feedback was saved.');
        appendMessage('bot', 'Goodbye — I will keep learning.');
        const btn = document.createElement('button');
        btn.innerText = 'Start Over';
        btn.onclick = () => resetConversation();
        inputArea.appendChild(btn);
      }).catch(e => {
        appendMessage('bot', 'Sorry, I could not save your feedback.');
        const btn = document.createElement('button');
        btn.innerText = 'Start Over';
        btn.onclick = () => resetConversation();
        inputArea.appendChild(btn);
      });
    } catch (e) {
      appendMessage('bot', 'Sorry, I could not save your feedback.');
    }
    return;
  }

  // no chat flow — fall back to original recipe flow for other fields

  // otherwise fall back to the original recipe flow
  originalProceed(lastField);
}

// Feedback section functionality
let selectedRating = 0;

function initializeFeedbackSection() {
  // Hide the feedback section initially - it will show after scrolling to instructions
  const feedbackSection = document.querySelector('.feedback-section');
  if (feedbackSection) {
    feedbackSection.classList.remove('visible');
  }
  
  // Set up scroll detection to show feedback section
  setupScrollDetection();
  
  const stars = document.querySelectorAll('.star');
  const submitBtn = document.getElementById('submit-feedback-btn');
  const feedbackText = document.getElementById('feedback-text');
  const thankYouDiv = document.getElementById('feedback-thank-you');
  const feedbackCard = document.querySelector('.feedback-card');
  
  // Star rating functionality
  stars.forEach((star, index) => {
    star.addEventListener('click', () => {
      selectedRating = index + 1;
      updateStarDisplay();
      updateSubmitButton();
    });
    
    star.addEventListener('mouseover', () => {
      highlightStars(index + 1);
    });
  });
  
  // Reset star display on mouse leave
  document.querySelector('.star-rating').addEventListener('mouseleave', () => {
    updateStarDisplay();
  });
  
  // Submit button functionality
  submitBtn.addEventListener('click', () => {
    submitFeedback();
  });
  
  // Optional: Enable submit with just text (no rating required)
  feedbackText.addEventListener('input', () => {
    updateSubmitButton();
  });
}

function setupScrollDetection() {
  // Remove any existing scroll listeners
  const recipeDetailView = document.getElementById('recipe-detail-view');
  if (recipeDetailView) {
    recipeDetailView.removeEventListener('scroll', handleScrollForFeedback);
  }
  
  // Add scroll listener to the recipe detail view
  if (recipeDetailView) {
    recipeDetailView.addEventListener('scroll', handleScrollForFeedback);
  }
  
  // Also check if instructions are already visible (for short recipes)
  setTimeout(() => {
    checkInstructionsVisibility();
  }, 100);
}

function handleScrollForFeedback() {
  checkInstructionsVisibility();
}

function checkInstructionsVisibility() {
  const instructionsSection = document.getElementById('detail-instructions');
  const feedbackSection = document.querySelector('.feedback-section');
  
  if (!instructionsSection || !feedbackSection) return;
  
  const rect = instructionsSection.getBoundingClientRect();
  const recipeDetailView = document.getElementById('recipe-detail-view');
  
  if (!recipeDetailView) return;
  
  const containerRect = recipeDetailView.getBoundingClientRect();
  
  // Show feedback if instructions section is visible or user has scrolled past it
  const instructionsVisible = rect.top < containerRect.bottom && rect.bottom > containerRect.top;
  const scrolledPastInstructions = rect.bottom < containerRect.top;
  
  if (instructionsVisible || scrolledPastInstructions) {
    if (!feedbackSection.classList.contains('visible')) {
      feedbackSection.classList.add('visible');
      
      // Add a subtle animation when it appears
      feedbackSection.style.opacity = '0';
      feedbackSection.style.transform = 'translateY(20px)';
      
      setTimeout(() => {
        feedbackSection.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        feedbackSection.style.opacity = '1';
        feedbackSection.style.transform = 'translateY(0)';
      }, 50);
    }
  }
}

function highlightStars(rating) {
  const stars = document.querySelectorAll('.star');
  stars.forEach((star, index) => {
    if (index < rating) {
      star.classList.add('active');
    } else {
      star.classList.remove('active');
    }
  });
}

function updateStarDisplay() {
  highlightStars(selectedRating);
}

function updateSubmitButton() {
  const submitBtn = document.getElementById('submit-feedback-btn');
  const feedbackText = document.getElementById('feedback-text');
  
  // Enable submit if user has selected a rating OR entered text
  if (selectedRating > 0 || feedbackText.value.trim()) {
    submitBtn.disabled = false;
  } else {
    submitBtn.disabled = true;
  }
}

function submitFeedback() {
  const feedbackText = document.getElementById('feedback-text').value.trim();
  const thankYouDiv = document.getElementById('feedback-thank-you');
  const feedbackForm = document.querySelector('.feedback-card > *:not(.feedback-thank-you)');
  
  // Prepare feedback data
  const feedbackData = {
    rating: selectedRating,
    comment: feedbackText,
    timestamp: new Date().toISOString(),
    recipe: getCurrentRecipeName() // Get current recipe name
  };
  
  // Send feedback to server (if API exists)
  fetch('/api/recipe-feedback', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(feedbackData)
  }).then(response => {
    // Show thank you message regardless of server response
    showThankYouMessage();
  }).catch(error => {
    console.log('Feedback saved locally:', feedbackData);
    // Show thank you message even if server is unavailable
    showThankYouMessage();
  });
}

function showThankYouMessage() {
  const thankYouDiv = document.getElementById('feedback-thank-you');
  const formElements = document.querySelectorAll('.star-rating-container, .feedback-input-container, .submit-feedback-btn');
  
  // Hide form elements
  formElements.forEach(element => {
    element.style.display = 'none';
  });
  
  // Show thank you message
  thankYouDiv.style.display = 'block';
  
  // Optional: Auto-hide after a few seconds
  setTimeout(() => {
    const feedbackSection = document.getElementById('recipe-feedback-section');
    if (feedbackSection) {
      feedbackSection.style.opacity = '0.7';
      feedbackSection.style.pointerEvents = 'none';
    }
  }, 3000);
}

function getCurrentRecipeName() {
  const titleElement = document.getElementById('detail-title');
  return titleElement ? titleElement.textContent : 'Unknown Recipe';
}

function resetFeedbackSection() {
  selectedRating = 0;
  const stars = document.querySelectorAll('.star');
  const submitBtn = document.getElementById('submit-feedback-btn');
  const feedbackText = document.getElementById('feedback-text');
  const thankYouDiv = document.getElementById('feedback-thank-you');
  const formElements = document.querySelectorAll('.star-rating-container, .feedback-input-container, .submit-feedback-btn');
  const feedbackSection = document.getElementById('recipe-feedback-section');
  
  // Hide the feedback section during reset
  const feedbackSectionVisible = document.querySelector('.feedback-section');
  if (feedbackSectionVisible) {
    feedbackSectionVisible.classList.remove('visible');
    // Reset animation styles
    feedbackSectionVisible.style.opacity = '';
    feedbackSectionVisible.style.transform = '';
    feedbackSectionVisible.style.transition = '';
  }
  
  // Reset all elements
  stars.forEach(star => star.classList.remove('active'));
  if (feedbackText) feedbackText.value = '';
  if (submitBtn) submitBtn.disabled = true;
  if (thankYouDiv) thankYouDiv.style.display = 'none';
  
  // Show form elements
  formElements.forEach(element => {
    element.style.display = '';
  });
  
  // Reset section opacity and pointer events
  if (feedbackSection) {
    feedbackSection.style.opacity = '';
    feedbackSection.style.pointerEvents = '';
  }
  
  // Remove existing scroll listeners
  const recipeDetailView = document.getElementById('recipe-detail-view');
  if (recipeDetailView) {
    recipeDetailView.removeEventListener('scroll', handleScrollForFeedback);
  }
}

// Loading animation functions
function showLoadingAnimation() {
  const overlay = document.getElementById('loading-overlay');
  if (overlay) {
    overlay.style.display = 'flex';
  }
}

function hideLoadingAnimation() {
  const overlay = document.getElementById('loading-overlay');
  if (overlay) {
    overlay.style.display = 'none';
  }
}

// New functions for improved UI flow
function showIngredientsInput() {
  clearInputArea();
  
  const container = document.createElement('div');
  container.className = 'choices';
  container.id = 'ingredients-container';
  
  // show a text box for custom ingredients
  const customWrap = document.createElement('div');
  customWrap.className = 'custom-ingredients-wrap';
  const customInput = document.createElement('input');
  customInput.type = 'text';
  customInput.placeholder = 'Type ingredients (comma separated) or leave blank to use the checkboxes';
  customInput.className = 'custom-ingredients';
  customWrap.appendChild(customInput);
  container.appendChild(customWrap);
  
  // show checkbox list of common ingredients
  const ingredientsList = ['Potato','Tomato','Onion','Carrot','Capsicum','Broccoli','Chicken','Egg','Fish','Paneer','Tofu','Lentils','Chickpeas','Bread','Pasta','Spinach'];
  const grid = document.createElement('div');
  grid.className = 'ingredient-grid';
  ingredientsList.forEach(item => {
    const label = document.createElement('label');
    label.className = 'ing-label';
    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.value = item.toLowerCase();
    cb.className = 'ing-checkbox';
    label.appendChild(cb);
    label.appendChild(document.createTextNode(' ' + item));
    grid.appendChild(label);
  });
  container.appendChild(grid);
  
  // Select button collects selections
  const done = document.createElement('button');
  done.type = 'button';
  done.innerText = 'Select';
  done.className = 'select-button';
  done.addEventListener('click', () => {
    const textVal = customInput.value.trim();
    const checked = Array.from(grid.querySelectorAll('.ing-checkbox:checked')).map(x => x.value);
    if (!textVal && checked.length === 0) {
      alert('Please select at least one ingredient or type them in the box.');
      return;
    }
    const val = textVal ? textVal : checked.join(', ');
    state['ingredients'] = val;
    recipeProceed('ingredients');
  });
  
  customInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      done.click();
    }
  });
  
  container.appendChild(done);
  inputArea.appendChild(container);
}

function showCuisineChoicesAlwaysVisible() {
  const container = document.createElement('div');
  container.className = 'choices always-visible';
  container.id = 'cuisine-choices-always';
  
  const label = document.createElement('div');
  label.className = 'choice-label';
  label.textContent = 'Choose Cuisine:';
  container.appendChild(label);
  
  const cuisines = ['Indian', 'Italian', 'Mediterranean', 'Mexican', 'Chinese', 'Thai'];
  cuisines.forEach(cuisine => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.innerText = cuisine;
    btn.className = 'choice-btn';
    btn.addEventListener('click', () => {
      if (state.selectedCuisine) return;
      state.cuisine = cuisine;
      state.selectedCuisine = true;
      btn.classList.add('selected');
      disableButtonContainer('cuisine-choices-always');
    });
    container.appendChild(btn);
  });
  
  inputArea.appendChild(container);
}

function showDifficultyChoicesAlwaysVisible() {
  const container = document.createElement('div');
  container.className = 'choices always-visible';
  container.id = 'difficulty-choices-always';
  
  const label = document.createElement('div');
  label.className = 'choice-label';
  label.textContent = 'Choose Difficulty:';
  container.appendChild(label);
  
  const difficulties = ['easy', 'moderate', 'complex'];
  difficulties.forEach(difficulty => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.innerText = difficulty;
    btn.className = 'choice-btn';
    btn.addEventListener('click', () => {
      if (state.selectedDifficulty) return;
      state.difficulty = difficulty;
      state.selectedDifficulty = true;
      btn.classList.add('selected');
      disableButtonContainer('difficulty-choices-always');
      
      // Show loading animation for difficulty selection
      showLoadingAnimation();
      setTimeout(() => {
        hideLoadingAnimation();
        // Auto-proceed if we have ingredients
        if (state.ingredients) {
          recipeProceed('difficulty');
        }
      }, 2500);
    });
    container.appendChild(btn);
  });
  
  inputArea.appendChild(container);
}

function askForIngredients() {
  appendMessage('bot', "What ingredients do you have available? You can type them or choose from the options below:");
  
  setTimeout(() => {
    showIngredientsInput();
  }, 500);
}

function askForCuisine() {
  appendMessage('bot', "Great! What type of cuisine would you like to explore today?");
  
  setTimeout(() => {
    showCuisineButtons();
  }, 500);
}

function askForDifficulty() {
  appendMessage('bot', "Perfect! How challenging would you like this recipe to be?");
  
  setTimeout(() => {
    showDifficultyButtons();
  }, 500);
}

function showIngredientsInput() {
  clearInputArea();
  
  const container = document.createElement('div');
  container.className = 'chat-input-container';
  
  // Create text input
  const inputWrapper = document.createElement('div');
  inputWrapper.className = 'ingredient-input-wrapper';
  
  const textInput = document.createElement('input');
  textInput.type = 'text';
  textInput.placeholder = 'Type ingredients (e.g., chicken, tomato, onion)';
  textInput.className = 'ingredient-text-input';
  inputWrapper.appendChild(textInput);
  
  const submitBtn = document.createElement('button');
  submitBtn.innerText = 'Continue';
  submitBtn.className = 'chat-submit-btn';
  submitBtn.onclick = () => {
    const ingredients = textInput.value.trim();
    if (ingredients) {
      state.ingredients = ingredients;
      appendMessage('user', `I have: ${ingredients}`);
      clearInputArea();
      setTimeout(() => askForCuisine(), 800);
    } else {
      alert('Please enter some ingredients');
    }
  };
  inputWrapper.appendChild(submitBtn);
  container.appendChild(inputWrapper);
  
  // Add quick selection buttons
  const quickOptions = document.createElement('div');
  quickOptions.className = 'quick-ingredients';
  quickOptions.innerHTML = '<div class="quick-label">Or choose common ingredients:</div>';
  
  const commonIngredients = ['Chicken', 'Vegetables', 'Pasta', 'Rice', 'Fish', 'Eggs'];
  commonIngredients.forEach(ingredient => {
    const btn = document.createElement('button');
    btn.innerText = ingredient;
    btn.className = 'quick-ingredient-btn';
    btn.onclick = () => {
      state.ingredients = ingredient.toLowerCase();
      appendMessage('user', `I want to cook with: ${ingredient}`);
      clearInputArea();
      setTimeout(() => askForCuisine(), 800);
    };
    quickOptions.appendChild(btn);
  });
  
  container.appendChild(quickOptions);
  inputArea.appendChild(container);
  
  // Add fade-in animation
  container.style.opacity = '0';
  setTimeout(() => {
    container.style.transition = 'opacity 0.5s ease';
    container.style.opacity = '1';
  }, 100);
  
  textInput.focus();
  
  // Handle Enter key
  textInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      submitBtn.click();
    }
  });
}

function showCuisineButtons() {
  clearInputArea();
  
  const container = document.createElement('div');
  container.className = 'chat-buttons-container';
  
  const cuisines = ['Indian', 'Italian', 'Mexican', 'Chinese', 'Mediterranean', 'American'];
  cuisines.forEach((cuisine, index) => {
    const btn = document.createElement('button');
    btn.innerText = cuisine;
    btn.className = 'chat-choice-btn';
    btn.onclick = () => {
      state.cuisine = cuisine;
      appendMessage('user', cuisine);
      clearInputArea();
      setTimeout(() => askForDifficulty(), 800);
    };
    
    // Staggered animation
    btn.style.opacity = '0';
    btn.style.transform = 'translateY(20px)';
    setTimeout(() => {
      btn.style.transition = 'all 0.3s ease';
      btn.style.opacity = '1';
      btn.style.transform = 'translateY(0)';
    }, index * 100);
    
    container.appendChild(btn);
  });
  
  inputArea.appendChild(container);
}

function showDifficultyButtons() {
  clearInputArea();
  
  const container = document.createElement('div');
  container.className = 'chat-buttons-container';
  
  const difficulties = [
    { key: 'easy', label: 'Easy (15-20 min)', desc: 'Simple and quick' },
    { key: 'moderate', label: 'Moderate (30-45 min)', desc: 'Some cooking skills needed' },
    { key: 'complex', label: 'Complex (60+ min)', desc: 'For experienced cooks' }
  ];
  
  difficulties.forEach((diff, index) => {
    const btn = document.createElement('button');
    btn.className = 'chat-choice-btn difficulty-btn';
    btn.innerHTML = `
      <div class="difficulty-label">${diff.label}</div>
      <div class="difficulty-desc">${diff.desc}</div>
    `;
    btn.onclick = () => {
      state.difficulty = diff.key;
      appendMessage('user', diff.label);
      clearInputArea();
      
      // Show loading animation
      showLoadingAnimation();
      
      setTimeout(() => {
        hideLoadingAnimation();
        appendMessage('bot', "Perfect! Let me find some amazing recipes for you...");
        setTimeout(() => generateRecipes(), 1000);
      }, 2000);
    };
    
    // Staggered animation
    btn.style.opacity = '0';
    btn.style.transform = 'translateY(20px)';
    setTimeout(() => {
      btn.style.transition = 'all 0.3s ease';
      btn.style.opacity = '1';
      btn.style.transform = 'translateY(0)';
    }, index * 150);
    
    container.appendChild(btn);
  });
  
  inputArea.appendChild(container);
}

function showCompactChoicesContainer() {
  clearInputArea();
  
  // Create main compact container
  const mainContainer = document.createElement('div');
  mainContainer.className = 'compact-choices-container';
  
  // Add ingredients section
  const ingredientsSection = createIngredientsSection();
  mainContainer.appendChild(ingredientsSection);
  
  // Add cuisine section
  const cuisineSection = createCuisineSection();
  mainContainer.appendChild(cuisineSection);
  
  // Add difficulty section
  const difficultySection = createDifficultySection();
  mainContainer.appendChild(difficultySection);
  
  inputArea.appendChild(mainContainer);
  ensureInputVisible();
}

function createIngredientsSection() {
  const section = document.createElement('div');
  section.className = 'compact-section';
  section.id = 'ingredients-container';
  
  const label = document.createElement('div');
  label.className = 'choice-label';
  label.textContent = 'Ingredients:';
  section.appendChild(label);
  
  // show a text box for custom ingredients
  const customWrap = document.createElement('div');
  customWrap.className = 'custom-ingredients-wrap';
  const customInput = document.createElement('input');
  customInput.type = 'text';
  customInput.placeholder = 'Type ingredients (comma separated) or leave blank to use checkboxes';
  customInput.className = 'custom-ingredients';
  customWrap.appendChild(customInput);
  section.appendChild(customWrap);
  
  // show checkbox list of common ingredients
  const ingredientsList = ['Potato','Tomato','Onion','Carrot','Capsicum','Broccoli','Chicken','Egg','Fish','Paneer','Tofu','Lentils','Chickpeas','Bread','Pasta','Spinach'];
  const grid = document.createElement('div');
  grid.className = 'ingredient-grid';
  ingredientsList.forEach(item => {
    const label = document.createElement('label');
    label.className = 'ing-label';
    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.value = item.toLowerCase();
    cb.className = 'ing-checkbox';
    label.appendChild(cb);
    label.appendChild(document.createTextNode(' ' + item));
    grid.appendChild(label);
  });
  section.appendChild(grid);
  
  // Select button collects selections
  const done = document.createElement('button');
  done.type = 'button';
  done.innerText = 'Select Ingredients';
  done.className = 'choice-btn';
  done.addEventListener('click', () => {
    const textVal = (customInput && customInput.value && customInput.value.trim()) ? customInput.value.trim() : '';
    const checked = Array.from(grid.querySelectorAll('.ing-checkbox:checked')).map(x => x.value);
    if (!textVal && checked.length === 0) {
      alert('Please select at least one ingredient or type them in the box.');
      return;
    }
    const val = textVal ? textVal : checked.join(', ');
    state['ingredients'] = val;
    done.classList.add('selected');
    disableSection('ingredients-container');
    recipeProceed('ingredients');
  });
  
  customInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      done.click();
    }
  });
  
  section.appendChild(done);
  return section;
}

function createCuisineSection() {
  const section = document.createElement('div');
  section.className = 'compact-section';
  section.id = 'cuisine-choices-compact';
  
  const label = document.createElement('div');
  label.className = 'choice-label';
  label.textContent = 'Choose Cuisine:';
  section.appendChild(label);
  
  const cuisines = ['Indian', 'Italian', 'Mexican', 'Chinese', 'Mediterranean'];
  cuisines.forEach(cuisine => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.innerText = cuisine;
    btn.className = 'choice-btn';
    btn.addEventListener('click', () => {
      if (state.selectedCuisine) return;
      state.cuisine = cuisine;
      state.selectedCuisine = true;
      btn.classList.add('selected');
      disableSection('cuisine-choices-compact');
    });
    section.appendChild(btn);
  });
  
  return section;
}

function createDifficultySection() {
  const section = document.createElement('div');
  section.className = 'compact-section';
  section.id = 'difficulty-choices-compact';
  
  const label = document.createElement('div');
  label.className = 'choice-label';
  label.textContent = 'Choose Difficulty:';
  section.appendChild(label);
  
  const difficulties = ['easy', 'moderate', 'complex'];
  difficulties.forEach(difficulty => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.innerText = difficulty;
    btn.className = 'choice-btn';
    btn.addEventListener('click', () => {
      if (state.selectedDifficulty) return;
      state.difficulty = difficulty;
      state.selectedDifficulty = true;
      btn.classList.add('selected');
      disableSection('difficulty-choices-compact');
      
      showLoadingAnimation();
      setTimeout(() => {
        hideLoadingAnimation();
        if (state.ingredients && state.cuisine && state.difficulty) {
          generateRecipes();
        }
      }, 2000);
    });
    section.appendChild(btn);
  });
  
  return section;
}

function disableSection(sectionId) {
  const section = document.getElementById(sectionId);
  if (section) {
    const buttons = section.querySelectorAll('.choice-btn');
    buttons.forEach(btn => {
      if (!btn.classList.contains('selected')) {
        btn.disabled = true;
      }
    });
  }
}

// start
startConversation();
