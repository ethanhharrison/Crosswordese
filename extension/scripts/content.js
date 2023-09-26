console.log("HI");
const getAlternateClue = function (clue_text) {
  return "Testing for now lol";
};
const swapClue = function (text) {
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
    if (
      alternateClue.style.display === "" ||
      alternateClue.style.display === "none"
    ) {
      console.log("Swapping Clues!");
      actualClue.style.display = "none";
      alternateClue.style.display = "block";
    } else {
      console.log("Swapping Back!");
      actualClue.style.display = "block";
      alternateClue.style.display = "none";
    }
  };
};

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
    alternateClueButton.onclick = swapClue(clueText);
    clue.appendChild(alternateClueButton);
  });
  // Create a modal interface warning the user that they are trying to show an easier clue
  
}
