# Craig's Hackathon Project 2024-10

## To Do

-   [ ] Debug why it hangs on directory load sometimes

## Someday/Maybe

-   [ ] Show an hourglass or something when waiting for things.
-   [ ] Support using ssh keys, e.g. id_rsa, if someone asks for it

## Done

-   [x] Save location of USFM directory instead of hard-coding it.
-   [x] Save settings needed by Git, such as user name and email.
-   [x] Don't use local git client, use something like gitlib instead.
    -   [x] Add files to staging.
    -   [x] Commit staged files.
    -   [x] Push files to server.
-   [x] Don't use sed to make changes to files, do it within the app.
