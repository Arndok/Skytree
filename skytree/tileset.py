"""Definition of a Drawable Component with a tiled canvas and ability to select which of those tiles is drawn on any given moment."""

from pygame import Rect
from .helpers import repack2
from .drawable import Drawable

class TileSet(Drawable):
    """
    Extend Drawable to include tileset functionalities.
    
    Inherits all behaviour from Component, Positional and Drawable.
    
    Given some 2D tile dimensions, divides the image in squares and saves a list of tile-sized frames.
    
    Public methods:
    set_render(pos, idx): reposition the entity if needed; select frame from given index.
    hot_draw(canvas, pos, idx): perform set_render(pos, idx) and then draw(canvas).
    """
    
    def __init__(self, canvas, tile_dim, **kwargs):
        """
        Extend Drawable to set up correct frame dimensions and construct list of tiles.
        
        canvas is a Drawable canvas (raises ValueError if None).
        tile_dim can be either a tuple(width, height) or a single number (for square tiles).
        """
        if canvas is None:
            raise ValueError("TileSet constructor received an empty canvas.")
        tile_dim = repack2(tile_dim)
        super().__init__(canvas, frame=tile_dim, **kwargs)
        
        self._frames = tuple(Rect((i, j), (tile_dim)) \
                        for j in range(0, self.draw_rect.height, tile_dim[1]) \
                          for i in range(0, self.draw_rect.width, tile_dim[0]))
        """A matrix of rectangles framing each tile in the sheet."""
        
    @property
    def width(self):
        """Tile width (from frame)."""
        return self.frame.width
        
    @property
    def height(self):
        """Tile height (from frame)."""
        return self.frame.height
        
    @property
    def dim(self):
        """Tile 2D dimensions (from frame)."""
        return tuple((self.frame.width, self.frame.height))
        
    @property
    def sheet_width(self):
        """Sheet width (from canvas)."""
        return self.canvas.width
        
    @property
    def sheet_height(self):
        """Sheet height (from canvas)."""
        return self.canvas.height
        
    @property
    def sheet_dim(self):
        """Sheet 2D dimensions (from canvas)."""
        return tuple((self.canvas.width, self.canvas.height))
        
    @property
    def frames(self):
        """Public reference to the matrix of frames (read-only)."""
        return self._frames
        
    def set_render(self, pos=None, idx=0):
        """
        Reposition the entity if needed and select frame from given index.
        
        Repositioning is used by sprites, since they're not subsurfaces and they're moving.
        """
        if pos:
            self.pos = pos
        self.frame = self._frames[idx]
        
    def hot_draw(self, canvas, pos=None, idx=0):
        """Perform set_render(pos, idx) and then draw(canvas)."""
        self.set_render(pos, idx)
        self.draw(canvas)
        