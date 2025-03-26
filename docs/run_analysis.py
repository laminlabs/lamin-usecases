import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import scvi
import matplotlib.pyplot as plt
import seaborn as sns
from torch_geometric.data import HeteroData
from torch_geometric.nn import HeteroConv, SAGEConv
from captum.attr import IntegratedGradients
import copy

def train_scvi_model(adata, batch_key="patient", layer="counts", epochs=5):
    """Prepares and trains an scVI model to extract latent representations."""
    scvi.model.SCVI.setup_anndata(adata, batch_key=batch_key, layer=layer)
    model = scvi.model.SCVI(adata, gene_likelihood='nb', dispersion="gene")
    model.train(max_epochs=epochs)
    return model

def prepare_tensors(adata):
    """Converts scVI embeddings and cell labels into PyTorch tensors."""
    X_latent = torch.tensor(adata.obsm["X_scVI"], dtype=torch.float)
    binary_labels = np.where(adata.obs["site"].values == "primary", 0, 1)
    cell_tensor = torch.tensor(binary_labels, dtype=torch.long)
    return X_latent, cell_tensor

def create_graph(adata, cell_features, n_cells, cell_labels, expr_threshold=1):
    """Constructs a bipartite graph where edges are based on gene expression levels."""
    data = HeteroData()
    data['cell'].x = cell_features

    # random learnable embeddings for gene nodes
    gene_features = torch.randn(len(adata.var_names), 32, requires_grad=True)
    data['gene'].x = gene_features

    # get raw expression values
    X_raw = adata.layers["counts"] if "counts" in adata.layers else adata.X
    X_raw = X_raw.toarray() if hasattr(X_raw, "toarray") else X_raw

    # edges where expression > threshold
    edge_index = [[], []]
    for i in range(n_cells):
        expressed_genes = np.where(X_raw[i, :] > expr_threshold)[0]
        edge_index[0].extend([i] * len(expressed_genes))
        edge_index[1].extend(expressed_genes)

    edge_index = torch.tensor(edge_index, dtype=torch.long)
    data['cell', 'expresses', 'gene'].edge_index = edge_index
    data['gene', 'expressed_by', 'cell'].edge_index = edge_index[[1, 0]]

    data['cell'].y = cell_labels
    return data

class HeteroGNN(nn.Module):
    def __init__(self, cell_in_dim, gene_in_dim, hidden_dim, out_dim):
        super(HeteroGNN, self).__init__()
        self.conv1 = HeteroConv({
            ('cell', 'expresses', 'gene'): SAGEConv((cell_in_dim, gene_in_dim), hidden_dim),
            ('gene', 'expressed_by', 'cell'): SAGEConv((gene_in_dim, cell_in_dim), hidden_dim),
        }, aggr='mean')

        self.conv2 = HeteroConv({
            ('cell', 'expresses', 'gene'): SAGEConv((hidden_dim, hidden_dim), hidden_dim),
            ('gene', 'expressed_by', 'cell'): SAGEConv((hidden_dim, hidden_dim), hidden_dim),
        }, aggr='mean')

        self.lin = nn.Linear(hidden_dim, out_dim)
    
    def forward(self, data):
        x_dict = {node_type: data[node_type].x for node_type in data.node_types}
        edge_index_dict = {etype: data[etype].edge_index for etype in data.edge_types}
        x_dict = self.conv1(x_dict, edge_index_dict)
        x_dict = {key: F.relu(val) for key, val in x_dict.items()}
        x_dict = self.conv2(x_dict, edge_index_dict)
        x_dict = {key: F.relu(val) for key, val in x_dict.items()}
        return self.lin(x_dict['cell']), x_dict
    
# training loop
def train(model, optimizer, criterion, graph_data):
    model.train()
    optimizer.zero_grad()
    out, _ = model(graph_data)
    loss = criterion(out, graph_data['cell'].y)
    loss.backward()
    optimizer.step()
    return loss.item(), model

def test(model, graph_data):
    model.eval()
    with torch.no_grad():
        out, _ = model(graph_data)
        pred = out.argmax(dim=1)
        accuracy = (pred == graph_data['cell'].y).sum().item() / graph_data['cell'].num_nodes
    return accuracy

def run_analysis(adata, epochs, learning_rate):
    # scVI and extract latent representation
    model = train_scvi_model(adata)
    latent = model.get_latent_representation()
    adata.obsm["X_scVI"] = latent  # store in AnnData
    cell_features, cell_labels = prepare_tensors(adata)
    n_cells, latent_dim = cell_features.shape

    # construct graph
    graph_data = create_graph(adata, cell_features, n_cells, cell_labels)
    # instantiate model
    GNN_model = HeteroGNN(cell_in_dim=latent_dim, gene_in_dim=32, hidden_dim=64, out_dim=2)
    optimizer = optim.Adam(GNN_model.parameters(), lr=learning_rate)
    criterion = nn.CrossEntropyLoss()

    # train and evaluate
    for epoch in range(epochs):
        loss, GNN_model = train(GNN_model, optimizer, criterion, graph_data)
        if epoch % 10 == 0:
            print(f"Epoch {epoch}, Loss: {loss:.4f}, Accuracy: {test(GNN_model, graph_data):.4f}")
    
    return GNN_model, graph_data
    
    