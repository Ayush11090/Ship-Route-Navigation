import plotly.graph_objects as go

def plot_subgraph(subgraph, a_star_path,save_path="navigation_map.html" ):
    """Visualize subgraph and A* path using Plotly on a 3D globe"""
    node_lons = [n[0] for n in subgraph.nodes()]
    node_lats = [n[1] for n in subgraph.nodes()]
    
    path_lons = [n[0] for n in a_star_path]
    path_lats = [n[1] for n in a_star_path]

    edge_lons, edge_lats = [], []
    for u, v in subgraph.edges():
        edge_lons += [u[0], v[0], None]
        edge_lats += [u[1], v[1], None]

    fig = go.Figure()

    fig.add_trace(go.Scattergeo(
        lon=edge_lons, lat=edge_lats,
        mode='lines', line=dict(width=0.5, color='gray'),
        name='Shipping Routes'
    ))

    fig.add_trace(go.Scattergeo(
        lon=node_lons, lat=node_lats,
        mode='markers', marker=dict(size=2, color='blue', opacity=0.3),
        name='Navigable Nodes'
    ))

    fig.add_trace(go.Scattergeo(
        lon=path_lons, lat=path_lats,
        mode='lines+markers', line=dict(width=2, color='red'),
        marker=dict(size=4, color='red'),
        name='Optimal Path'
    ))

    fig.update_layout(
        geo=dict(
            projection_type='orthographic',
            showland=True,
            landcolor='rgb(100, 100, 100)',
            oceancolor='rgb(0, 0, 80)',
            showocean=True,
            showcountries=True,
            countrycolor='rgb(200, 200, 200)'
        ),
        title='Marine Navigation Network with Optimal Route',
        width=1200,
        height=800
    )
    fig.show()
    fig.write_html(save_path)