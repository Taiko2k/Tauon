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

- Website design.

- Gstreamer backend. Do you know your way around gstreamer and would like to see this project become fully free software? Then you
could help replace the existing BASS backend with a Gstreamer backend. There is already a basic implimentation in place which can
be enabled by passing -gst as an argument. The following expansions are needed:

    | Required          | Bonus         |
    | ------------- |:-------------:| 
    | crossfade      | Inbound streaming |
    | fade-in, out   | Outbund streaming      | 
    | ftt data and binning for visualiser | Gapless playback |
    | level data for visualiser |
