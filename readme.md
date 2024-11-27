# How to Use This App

## Preparing for use

From WACS, clone a repo that you control to your local storage.

For example, I copied the WycliffeAssociates/en_ulb to my WACS account
and then cloned it to my SSD. If you didn't clone the repos from your
personal account you won't have the rights to push changes to it later.

## Running the App

1.  Unzip the app into a directory.
2.  Double-click `main.exe` (Windows) or `main` (Linux) to launch the
    app. (You can also call it from the command line with `--trace` to
    get detailed info about what the app is doing while it runs.)
3.  The main window will appear.

## Reading a directory of USFM files

1.  Click the "Load USFM" button.
2.  Using the file picker, navigate to the directory of the repo you
    cloned and click the "Choose" button. In my case, the repo directory
    was called `en_ulb_craig`.
3.  The app will show "Reading USFM files" for a few seconds, and then
    "Finished reading USFM." If you ran with the `--trace` command line
    parameter, you can watch it iterate through the files.
4.  A list of words by count will appear.

## Correcting spelling of a word

1.  Select a word from the list. I like to go to the bottom of the list
    and choose a rare word like "crystal-clear".
2.  All occurrences of the word should appear in the content pane.
3.  Click "Fix Spelling". A dialog will appear asking for the
    correction.
4.  Correct the spelling of the word in the text field.
5.  Click "OK".
6.  The app will display updates as it updates each file containing that
    word. If you ran with the `--trace` parameter you can see more info
    in the console.

## Uploading changes

1.  Click "Push changes."
2.  The app may request some information from you:
    -   Git commit name, e.g. "John Doe"
    -   Git email address, e.g. "john@example.org"
    -   WACS user id, e.g. "johnd"
    -   WACS password. (The app will remember your password while it's
        running, but does not store it anywhere between runs.)
3.  The app will update as it pushes the files to WACS. If there is an
    error, it will appear in the status bar and the console.

## Thank you!

That's it -- have fun, and thank you for testing this app!

# To Do

## Someday/Maybe

-   [ ] Possible edge case -- correcting the spelling of small words
        like "the" can affect words like "them"
-   [ ] Show an hourglass or something when waiting for things.
-   [ ] Support using ssh keys, e.g. id_rsa, if someone asks for it

## Done

-   [x] Save location of USFM directory instead of hard-coding it.
-   [x] Save settings needed by Git, such as user name and email.
-   [x] Don't use local git client, use something like gitlib instead.
    -   [x] Add files to staging.
    -   [x] Commit staged files.
    -   [x] Push files to server.
-   [x] Don't use sed to make changes to files, do it within the app.
-   [x] Debug why it hangs on directory load sometimes
-   [x] Update display with corrected word
