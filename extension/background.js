try {
  chrome.tabs.onUpdated.addListener(function (tabId, changeInfo, tab) {
    setTimeout(() => {
      if (changeInfo.status == "complete") {
        chrome.scripting.insertCSS({
          files: ["scripts/content-style.css"],
          target: { tabId: tab.id },
        });
        chrome.scripting.executeScript({
          files: ["scripts/content.js"],
          target: { tabId: tab.id },
        });
      }
    }, "1000");
  });
} catch (err) {
  console.log(err);
}
