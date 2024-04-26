import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
import pickle


data = pd.read_csv('/home/jack/uavMINDS6003/WildFires_DataSet.csv')


label_encoder = LabelEncoder()
data['CLASS'] = label_encoder.fit_transform(data['CLASS'])
X = data[['NDVI', 'LST', 'BURNED_AREA']].values
y = data['CLASS'].values


X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)


scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)


rf = RandomForestClassifier()
random_param = {
    'n_estimators': [200],
    'max_features': ['sqrt'],  
    'max_depth': [40],
    'min_samples_split': [2],
    'min_samples_leaf': [1]
}
random_search = RandomizedSearchCV(estimator=rf, param_distributions=random_param, n_iter=100, cv=3, verbose=2, random_state=42, n_jobs=-1)
random_search.fit(X_train_scaled, y_train)


best_rf_model = random_search.best_estimator_


y_pred = best_rf_model.predict(X_test_scaled)
accuracy = accuracy_score(y_test, y_pred)
print("Accuracy: ", accuracy)


with open('model.pkl', 'wb') as file:
    pickle.dump(best_rf_model, file)

with open('scaler.pkl', 'wb') as file:
    pickle.dump(scaler, file)

with open('label_encoder.pkl', 'wb') as file:
    pickle.dump(label_encoder, file)

print("Model, scaler, and label encoder have been saved.")
