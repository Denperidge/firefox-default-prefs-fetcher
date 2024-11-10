# firefox-default-preferences
A project that outputs the default Firefox preferences into JSON files.

If you just **need the data**, view [the releases](https://github.com/Denperidge/firefox-default-prefs-fetcher/releases/).

You can also download the latest data directly from [github.com/Denperidge/firefox-default-prefs-fetcher/releases/latest/download/linux-132.0.1-defaults.json](https://github.com/Denperidge/firefox-default-prefs-fetcher/releases/latest/download/linux-132.0-defaults.json), replacing linux and the firefox version number as desired.

## How-to
### Get a list of Firefox versions
Go to [mozilla.org/en-US/firefox/releases/](https://www.mozilla.org/en-US/firefox/releases/) and run the following script in the console
```js
let regex = /(\d.*?)(\/|.html)/;
let data = Array.from(document.querySelectorAll(".c-release-list li a")).map((a) => regex.exec(a.href)[1])

// Return last 85 versions, due to Github Actions strategy constraints. Remove splice to list all
console.log(JSON.stringify(data.splice(0, 85)))
```


### Install
This project uses [pdm](https://pdm-project.org/) for project management. 


