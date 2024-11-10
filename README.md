# firefox-default-preferences
A project that outputs the default Firefox preferences into JSON files.

If you just **need the data**, view [the releases](https://github.com/Denperidge/firefox-default-prefs-fetcher/releases/).

You can also download the latest data directly from [github.com/Denperidge/firefox-default-prefs-fetcher/releases/latest/download/linux-132.0.1-defaults.json](https://github.com/Denperidge/firefox-default-prefs-fetcher/releases/latest/download/linux-132.0-defaults.json), replacing linux and the firefox version number as desired.

## How-to
### Get a list of Firefox versions
Go to [ftp.mozilla.org/pub/firefox/releases/](https://ftp.mozilla.org/pub/firefox/releases/) and run the following script in the console
```js
let data = Array.from(document.querySelectorAll("tbody a")).map((a) => a.text.replace("/", ""))
data = data.filter(entry => entry.match(/\d*\.\d(\.\d*)/) != null);
data.sort((a,b) => {
    const aSplit = a.split(".")
	const bSplit = b.split(".")
	const length = aSplit.length > bSplit.length ? bSplit.length : aSplit.length;
	for (let i = 0; i < length; i++) {
        const aValue = parseInt(aSplit[i].replace(/\D/g, ""))
        const bValue = parseInt(bSplit[i].replace(/\D/g, ""))
	    if (aValue > bValue) {
		    return -1;  // A before b
	    }
        else if (aValue < bValue) {
            return 1;
        }
    }
	return 0;
})

// Return last 85 versions, due to Github Actions strategy constraints. Remove splice to list all
console.log(JSON.stringify(data.splice(0, 85)))
```


### Install
This project uses [pdm](https://pdm-project.org/) for project management. 


