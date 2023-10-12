head = document.querySelector("head");
head.insertAdjacentHTML("afterbegin",`<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>`);
import { ajax } from "jquery";

function getAlternateClue(clue_text) {
  return "Testing for now lol";
}
function getClueAnswer(clue_text) {
  ajax({
    type: "POST",
    url: "~/clue_solver.py",
    data: { param: clue_text },
    success: function(response)
    {
      console.log(response);
    },
    error: function()
    {
      alert("Could not solve clue");
    }
  });
}

function createModal(data) {
  return `
    <div class="modal-system-container">
      <div class="xwd__modal--wrapper">
        <div id="modalWrapper-overlay" role="none" class="xwd__modal--overlay"></div>
        <div role="textbox" class="xwd__modal--body animate-opening">
          <div role="button" aria-label="close" class="xwd__modal--close" tabindex="0">
            <i class="pz-icon pz-icon-close"></i>
          </div>
          <article class="xwd__modal--content>
            <h1 class="pz-moment__title medium karnak">Are You Sure?</h1>
            <div class="xwd__modal--button-container">
              <button type="button" class="pz-moment__button" aria-disabled="false" aria-label="Confirm">
                <span>Confirm</span>
              </button>
            </div>
          </article>
        </div>
      </div>
    </div>
  `;
}
function showModal() {
  var data = {};
  portalGameModals = document.querySelector("#portal-game-modals");
  portalGameModals.insertAdjacentHTML("afterbegin", createModal(data));
  // When the modal closing button is clicked, perform closing information and give info that
  // they don't want to see the new question
  modalCloseButton = document.querySelector(".xwd__modal--close");
  modalBody = document.querySelector(".xwd__modal--body");
  modalContainer = document.querySelector(".modal-system-container");
  modalCloseButton.onclick = function () {
    modalBody.classList.toggle("closing");
    setTimeout(() => modalContainer.remove(), 200);
    return false;
  };
}
function swapClue(text) {
  return function () {
    var allClues = document.querySelectorAll(".xwd__clue--text");
    var i = 0;
    var actualClue;
    while (allClues[i].innerHTML !== text && i < allClues.length) {
      i++;
    }
    actualClue = allClues[i];
    parentClue = actualClue.parentElement;
    alternateClue = parentClue.querySelector(".xwd__clue--alternate");
    clueButton = parentClue.querySelector(".xwd__clue--alternate-button");
    if (
      alternateClue.style.display === "" ||
      alternateClue.style.display === "none"
    ) {
      showModal();
      console.log("Swapping Clues!");
      actualClue.style.display = "none";
      alternateClue.style.display = "block";
      clueButton.innerHTML = "Hide";
    } else {
      console.log("Swapping Back!");
      actualClue.style.display = "block";
      alternateClue.style.display = "none";
      clueButton.innerHTML = "Show";
    }
  };
}

if (window.location.href.includes("nytimes.com/crosswords/game")) {
  const clueLists = document.querySelector(".xwd__layout--cluelists");
  const allClues = clueLists.querySelectorAll(".xwd__clue--li");
  // Create the new clues and buttons which allow for swapping clues
  allClues.forEach((clue) => {
    const clueText = clue.querySelector(".xwd__clue--text").innerHTML;
    const altClueText = getAlternateClue(clueText);
    // Make new element that has the alternate clue
    const alternateClue = document.createElement("span");
    alternateClue.className = "xwd__clue--alternate";
    alternateClue.innerHTML = altClueText;
    clue.appendChild(alternateClue);
    // Make button to allow for the current clue to swap with the alternate one
    const alternateClueButton = document.createElement("button");
    alternateClueButton.className = "xwd__clue--alternate-button";
    alternateClueButton.innerHTML = "Show";
    alternateClueButton.onclick =  getClueAnswer(clueText); // swapClue(clueText);
    clue.appendChild(alternateClueButton);
  });
}
