import cartopy.crs as ccrs
import matplotlib.pyplot as plt


def create_fig(
    title='',
    projection=ccrs.Robinson(central_longitude=0),
    shape=(1, 1),
    h=5,
    w=8,
):
    subplot_kw = {}
    if type(projection) != type(None):
        subplot_kw = {
            'projection': projection
        }

    fig, axs = plt.subplots(
        *shape,
        figsize=(w * shape[1], h * shape[0]),
        subplot_kw=subplot_kw
    )
    axs = axs.flatten() if shape[0] > 1 or shape[1] > 1 else [axs]
    title and fig.suptitle(title)

    return fig, axs


def draw_gridlines(ax):
    ax.gridlines(
        alpha=0.5,
        crs=ccrs.PlateCarree(),
        draw_labels=False,
        xlocs=[-135, -90, -45, 0, 45, 90, 135],
        ylocs=[-60, -30, 0, 30, 60]
    )

    # Draw grid labels
    gridlabels = ax.gridlines(
        crs=ccrs.PlateCarree(),
        draw_labels=['bottom', 'geo', 'left'],
        alpha=0,
        xlocs=[-90, 0, 90],
        ylocs=[-60, -30, 0, 30, 60],
        # xlabel_style={'rotation': 45, 'ha':'right'},
    )

    # Force draw to add label artists to gl2
    plt.draw()

    # Remove right hand side geo artists (-60, 60)
    for a in gridlabels.geo_label_artists:
        if a.get_position()[0] > 0:
            a.set_visible(False)
