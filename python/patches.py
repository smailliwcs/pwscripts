import matplotlib
import matplotlib.patheffects
import types

def fix(patch):
    patch.draw = types.MethodType(draw, patch)

def draw(self, renderer):
    if not self.get_visible():
        return

    renderer.open_group('patch', self.get_gid())
    gc = renderer.new_gc()

    gc.set_foreground(self._edgecolor, isRGBA=True)

    lw = self._linewidth
    if self._edgecolor[3] == 0:
        lw = 0
    gc.set_linewidth(lw)
    gc.set_dashes(self._dashoffset, self._dashes)

    gc.set_antialiased(self._antialiased)
    self._set_gc_clip(gc)
    gc.set_capstyle(self.get_capstyle())
    gc.set_snap(self.get_snap())

    rgbFace = self._facecolor
    if rgbFace[3] == 0:
        rgbFace = None  # (some?) renderers expect this as no-fill signal

    gc.set_alpha(self._alpha)

    if self._hatch:
        gc.set_hatch(self._hatch)
        if self._hatch_color is not None:
            try:
                gc.set_hatch_color(self._hatch_color)
            except AttributeError:
                # if we end up with a GC that does not have this method
                warnings.warn("Your backend does not support setting the "
                              "hatch color.")

    if self.get_sketch_params() is not None:
        gc.set_sketch_params(*self.get_sketch_params())

    # FIXME : dpi_cor is for the dpi-dependecy of the
    # linewidth. There could be room for improvement.
    #
    # dpi_cor = renderer.points_to_pixels(1.)
    self.set_dpi_cor(renderer.points_to_pixels(1.))
    path, fillable = self.get_path_in_displaycoord()

    if not matplotlib.cbook.iterable(fillable):
        path = [path]
        fillable = [fillable]

    affine = matplotlib.transforms.IdentityTransform()

    if self.get_path_effects():
        renderer = matplotlib.patheffects.PathEffectRenderer(self.get_path_effects(), renderer)

    for p, f in zip(path, fillable):
        if f:
            renderer.draw_path(gc, p, affine, rgbFace)
        else:
            renderer.draw_path(gc, p, affine, None)

    gc.restore()
    renderer.close_group('patch')
    self.stale = False
