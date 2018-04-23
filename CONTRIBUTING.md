# Contributing to Tauon Music Box

### Issues

Feel free to create new github issues or just causally send me an email. 

For crashes, it would be most helpful if you could replicate the crash and capture the traceback from terminal output.

### Suggestions

For suggestions; submit any same as above.

I may or may not impliment any suggestions. Also explaining how a feature would be integraged would be more helpful than vauge ideas.

### Code Contributions

The current code base is very messy, as such I don't expect any code contributions. If you really want to you should message me about
what you want to work on beforehand.

## Possible contribution projects

- Website design. Are you good at site design? Could you design a main site? This would be hosted at https://taiko2k.github.io/tauonmb/ Theres already a basic
site there to give you a a starting idea for design, but its up to you as long as its good and vaugly in keeping with the project design.

- Branding and Icon desgin. Either an upgrade of the current designs or an entire overhaul / renaming

- UI design concepts. If you have an idea for an interface refreash, I might like to see it. Big or small. But ideally
keeping all existing functionality and vaugly in keeping with current design language.

- Gstreamer backend. Do you know your way around gstreamer and would like to see this project become fully free software? Then you
could help replace the existing BASS backend with a Gstreamer backend. There is already a basic implimentation in place which can
be enabled by passing -gst as an argument. The following expansions are needed:

    | Required          | Bonus         |
    | ------------- |:-------------:| 
    | crossfade      | Inbound streaming |
    | fade-in, out   | Outbund streaming      | 
    | ftt data and binning for visualiser | Gapless playback |
    | level data for visualiser |
