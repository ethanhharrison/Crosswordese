// if (window.location.href.includes("nytimes.com/crosswords/game")) { 
//     const body = document.querySelector("body");
//     console.log(body)
//     const content = body.querySelector(".pz-content")
//     const game_section = content.querySelector("#crossword-container")
//     const game_wrapper = game_section.querySelector(".pz-game-wrapper")
//     const game_screen = game_wrapper.querySelector(".pz-game-screen")
//     const portal_game_modal = game_screen.children[1]
//     console.log(portal_game_modal)
//     // const start_game_button = portal_game_modal.querySelector(".modal-system-container")
//     //.querySelector(".xwd__modal--wrapper").querySelector(".xwd__modal--body")
//     // console.log(start_game_button)



//     // const game_field = game_screen.querySelector(".pz-game-field")
//     // console.log(game_field)
//     // const puzzle = game_field.children[0]
//     // // querySelector("xwd__layout_container") // .querySelector("div").querySelector("article")
//     // console.log(puzzle)
// }

const init = function() {
    const injectElement = document.createElement("div");
    injectElement.className = "test-element";
    injectElement.innerHTML = "Hello!";
    document.body.appendChild(injectElement);
}
init();