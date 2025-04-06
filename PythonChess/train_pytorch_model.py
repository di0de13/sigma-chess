import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset as TorchDataset
from datasets import load_from_disk # Load HF dataset from local diskfrom sklearn.preprocessing import StandardScaler # Optional: For feature scalingimport numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt
import os

# --- 配置 ---
DATASET_PATH = "chess_evaluation_dataset_simple" # Path where HF dataset was saved
MODEL_SAVE_PATH = "simple_chess_eval_model_pytorch.pth"
FEATURE_NAMES = [ # Must match generate_hf_dataset.py'w_pawn', 'w_knight', 'w_bishop', 'w_rook', 'w_queen','b_pawn', 'b_knight', 'b_bishop', 'b_rook', 'b_queen','turn', 'w_castle_k', 'w_castle_q', 'b_castle_k', 'b_castle_q', 'en_passant'
]
NUM_FEATURES = len(FEATURE_NAMES)
LABEL_COLUMN = 'score'
LEARNING_RATE = 0.001
BATCH_SIZE = 64
NUM_EPOCHS = 25
HIDDEN_LAYER_SIZES = [128, 64] # Example MLP structure# --- PyTorch Dataset Wrapper ---# Adapts the Hugging Face dataset for PyTorch DataLoaderclass ChessDatasetTorch(TorchDataset):def init(self, hf_dataset, feature_cols, label_col, scaler=None):
        self.features = np.array(hf_dataset[feature_cols], dtype=np.float32)
        self.labels = np.array(hf_dataset[label_col], dtype=np.float32).reshape(-1, 1) # Ensure label is 2D
        self.scaler = scalerif self.scaler:# Fit scaler only on training data if providedif not hasattr(self.scaler, 'mean_'): # Check if scaler is already fitted
                 print("Fitting StandardScaler...")
                 self.scaler.fit(self.features)
             print("Applying StandardScaler...")
             self.features = self.scaler.transform(self.features)
def len(self):return len(self.labels)
def getitem(self, idx):return torch.tensor(self.features[idx], dtype=torch.float32), \
               torch.tensor(self.labels[idx], dtype=torch.float32)

# --- PyTorch Model Definition (Simple MLP) ---class SimpleChessEvaluatorMLP(nn.Module):def init(self, input_size, hidden_sizes):super().
__init__
()
        layers = []
        in_size = input_sizefor h_size in hidden_sizes:
            layers.append(nn.Linear(in_size, h_size))
            layers.append(nn.ReLU())# layers.append(nn.Dropout(0.1)) # Optional: Add dropout for regularization
            in_size = h_size
        layers.append(nn.Linear(in_size, 1)) # Output layer for the score
        self.network = nn.Sequential(*layers)
def forward(self, x):return self.network(x)

# --- Training Function ---def train_model():
    print("Loading dataset from disk...")if not os.path.exists(DATASET_PATH):
         print(f"Error: Dataset not found at {DATASET_PATH}. Run generate_hf_dataset.py first.")return
    dataset_dict = load_from_disk(DATASET_PATH)
# Optional: Feature Scaling (often helpful for NNs)# scaler = StandardScaler()
    scaler = None # Keep it simple first, uncomment StandardScaler to use scaling
    print("Preparing DataLoaders...")
    train_dataset = ChessDatasetTorch(dataset_dict['train'], FEATURE_NAMES, LABEL_COLUMN, scaler=scaler)# Important: Use the same scaler (fitted on train data) for the validation set
    val_dataset = ChessDatasetTorch(dataset_dict['test'], FEATURE_NAMES, LABEL_COLUMN, scaler=scaler if scaler and hasattr(scaler, 'mean_') else None)
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)
    print(f"Number of features: {NUM_FEATURES}")
    print(f"Training samples: {len(train_dataset)}, Validation samples: {len(val_dataset)}")
# --- Model, Loss, Optimizer ---
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    model = SimpleChessEvaluatorMLP(NUM_FEATURES, HIDDEN_LAYER_SIZES).to(device)
    print("Model Structure:")
    print(model)
    criterion = nn.MSELoss() # Mean Squared Error for regression task
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
# --- Training Loop ---
    train_losses = []
    val_losses = []
    best_val_loss = float('inf')
    print("Starting training...")for epoch in range(NUM_EPOCHS):
        model.train() # Set model to training mode
        running_train_loss = 0.0
        train_pbar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{NUM_EPOCHS} [Train]")
for features, labels in train_pbar:
            features, labels = features.to(device), labels.to(device)
# Zero gradients
            optimizer.zero_grad()
# Forward pass
            outputs = model(features)
            loss = criterion(outputs, labels)
# Backward pass and optimize
            loss.backward()
            optimizer.step()
            running_train_loss += loss.item()
            train_pbar.set_postfix({'loss': loss.item()})
        avg_train_loss = running_train_loss / len(train_loader)
        train_losses.append(avg_train_loss)
# --- Validation Loop ---
        model.eval() # Set model to evaluation mode
        running_val_loss = 0.0
        val_pbar = tqdm(val_loader, desc=f"Epoch {epoch+1}/{NUM_EPOCHS} [Val]")with torch.no_grad(): # Disable gradient calculation for validationfor features, labels in val_pbar:
                features, labels = features.to(device), labels.to(device)
                outputs = model(features)
                loss = criterion(outputs, labels)
                running_val_loss += loss.item()
                val_pbar.set_postfix({'loss': loss.item()})
        avg_val_loss = running_val_loss / len(val_loader)
        val_losses.append(avg_val_loss)
        print(f"Epoch {epoch+1}/{NUM_EPOCHS} - Train Loss: {avg_train_loss:.4f}, Val Loss: {avg_val_loss:.4f}")
# Save the model if validation loss improvedif avg_val_loss < best_val_loss:
            print(f"Validation loss improved ({best_val_loss:.4f} -> {avg_val_loss:.4f}). Saving model...")
            torch.save(model.state_dict(), MODEL_SAVE_PATH) # Save only the model weights
            best_val_loss = avg_val_loss# Optional: Save scaler if used# if scaler:#    import joblib#    joblib.dump(scaler, "scaler.joblib")
    print("Training finished.")
# --- Plotting Losses ---
    plt.figure(figsize=(10, 5))
    plt.plot(range(1, NUM_EPOCHS + 1), train_losses, label='Training Loss')
    plt.plot(range(1, NUM_EPOCHS + 1), val_losses, label='Validation Loss')
    plt.xlabel('Epoch')
    plt.ylabel('MSE Loss')
    plt.title('Training and Validation Loss')
    plt.legend()
    plt.grid(True)
    plt.savefig("training_loss_curve.png")
    print("Loss curve saved to training_loss_curve.png")# plt.show() # Uncomment to display plot immediatelyif name == "__main__":
    train_model()