## Scraping
[x]- Add Upstream Requirements to scraping process
[ ]Add HTML Pages for Requirements and Upstream Reqs. 
   Should have: Backlinks. Upstream -> REQ, REQ->API-Element
[ ] Metadata parser
- AI interence layer

## Review Process (backend)
[ ] integrate review-ingest with github issues
[ ] automate review-ingest as much as possible
[ ] test with volunteer

## GUI
[ ] badges beside function overviews currently garble the function signature. Change badge positioning so that it doesn't interfere with readability.

## Class Canvas
[p] Tweak parameters to make the initial view more beautiful
[p] Streamline Event Handling. Currently, UI concepts are mixed. Left-click+drag has two meanings, depending on where you click it's marquee, or select & drag. Come up with a rich, consistent, intutive user interface model that still supports the node-growing feature.
[ More fluent zooming / eye candy: class boxes could increase/decrease in size or detail level more fluently, depending on mouse distance.
[p] Remove Attractors. It looks like module boxes are drawn back to where they started, even after dragging things around, they float back. Make it easier to rearrange items permanently.
[ ] Integrate canvas diagram into class views. They could replace the local SVG UML diagrams. Need to do: Define meaningful parameterization, decide whether to put hard restrictions on what can be displayed in the class diagrams
[ ] Extend the db that is actually being rendered. Currently, Links are only "inherits" or "uses"/"references". Details are lost. Future approach: keep info about the type of relationship (e.g. "creates", "consumes", "produces", "aggregates", "processes", and if it "processes" (e.g. by a method call with non-const reference) another class, provide the method name that performs the processing. Same for "consumes" (method parameter, called by value) or "produces" (for return value of method). The specifics need to be detailed.

## Recently Completed

### Class Canvas
- Canvas views can be saved to and loaded from graph-specific `localStorage`, preserving the exact set of displayed nodes and the selection state with stale-node and unavailable-storage fallbacks.
- Save/load controls are integrated into the canvas toolbar; loading reapplies visibility, selection, layout, and background framing.
- The obsolete upper-left “Federphysik-Karte” caption was removed to free toolbar space.
- Focus framing follows the selected class and keeps its visible next frontier in view, anchoring viewport expansion at the pointer.
- A focused visible class always renders at UML detail level 2 with a persistent double border.
- Holding a selected class previews its next frontier at detail level 2, with clearer opacity and a reduced-motion-aware pulsating teal halo; the preview ends immediately once dragging starts.
