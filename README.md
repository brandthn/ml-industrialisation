## TD2: Iteration sur un modèle

Dans ce TD, nous allons voir un problème d'apprentissage supervisé, sur lequel on va rajouter des sources de données et des features au fur et à mesure. <br/>
Nous voulons faire du code industrialisé, où nous pouvons itérer rapidement. <br/>
Il est fortement conseillé:
- De faire les étapes une par une, de "jouer le jeu" d'un projet qui évolue au cour du temps
- Pour chaque étape, de coder une solution, puis voir les refactos intéressantes. Attention: une erreur serait de se perdre en cherchant la perfection. 
- De faire du code modulaire, avec:
  - Un module téléchargeant les données (un data catalogue)
  - Un module construisant les features. Chaque "feature" a son module
  - Un module générant le model. Tous les modèles ont les méthodes ".fit(X, y)", ".predict"

Vous avez le fichier de test tests/test_model.py avec les tests que je ferai. <br/>
Les tests appellent, dans main.py, la fonction "make_predictions(config: dict) -> df_pred: pd.Dataframe"


Télécharger [le dataset](https://drive.google.com/file/d/1OFDGVqlmx-5-hE3Bnn-996LGpumScwOV/view?usp=sharing). <br/>
Il s'agît de ventes mensuelles d'une industrie fictive.

1) Coder un modèle "SameMonthLastYearSales", predisant, pour les ventes de item N pour un mois, les mêmes ventes qu'il a faites l'année dernière au même mois (pour août 2024 les mêmes ventes que l'item N a eu en août 2023)

2) Coder un modèle auto-regressif.

Re-activer le test en renommant `def tst_ridge_model` -> `def test_ridge_model`

On veut entraîner un vrai modèle ridge, qui se sert de 2 features "last_month" (les ventes au mois précédent M-1) et "same_month_last_year" (les ventes à M-12)

Coder le "build_feature" qui va générer ces différentes features autoregressive. <br/>
Utiliser le modèle sklearn Ridge()

3) Ajouter une feature au modèle auto-régressif: les ventes moyennes

Re-activer le test en renommant `def tst_ridge_model_adding_yearly_mean_sales` -> `def test_ridge_model_adding_yearly_mean_sales`

On pense que les ventes ne dépendent pas que des ventes au mois précédent ou au même mois l'année dernière, mais à la moyenne des ventes sur l'année.

Calculer la moyenne des ventes par mois sur l'année précédente
"last_year_average" = sum(sames(M-1:M-12)) / 12

4) Ajouter une feature au modèle auto-régressif: le growth factor

Re-activer le test en renommant `def tst_ridge_model__adding_growth_factor` -> `def test_ridge_model__adding_growth_factor`

Les données ont été générées comme une combinaison des ventes le même mois l'année dernière, des ventes moyennes sur l'année dernière, et des ventes du même mois l'année dernière fois la croissance du quarter Q-5 au quarter Q-1

$$sales(M) = a * sales(M-12) + b * sales(M-1:M-12) / 12 + c * sales(M-12) \frac{sales(M-1:M-3)}{sales(M-13:M-15)}$$

On va ajouter comme feature ce growth factor:
$$growth(M) = \frac{sales(M-1:M-3)}{sales(M-13:M-15}$$


5) Ajouter les données marketing.

Re-activer le test en renommant `def tst_marketing_model` -> `def test_marketing_model`

Les mois où il y a eu des dépenses marketing, cela a impacté les ventes.

Les données ont été générées ainsi

$$ sales(M) = ...past\, model... * (1 + marketing\_spend * d) $$

6) Ajouter les données de prix

Re-activer le test en renommant `def tst_price_model` -> `def test_price_model`

Les clients, des grossistes, sont prévenus en avance d'un changement de prix. <br/>
Si le prix va augmenter le mois suivant M+1, ils commandent plus que d'habitude au mois M, et moins au mois M+1. <br/<
A l'inverse, si le prix va baisser, ils commandent moins au mois M et plus à M+1.

7) Ajouter les données de stock

Re-activer le test en renommant `def tst_stock_model` -> `def test_stock_model`

Certains mois, l'industriel a eu des ruptures de stocks et donc a vendu moins que ce qu'il aurait pu. Le mois suivant, il a plus vendu car les clients ont racheté ce qu'ils devaient pour leur consommation. <br/>

stock.csv contient les "refill" de stock quotidien. On suppose que le stock initial était 0. <br/>
Il y a rupture de stock si le stock est 0 à la fin du mois. <br/>
En ayant identifié les ruptures de stock, vous pouvez décider de ne pas entraîner sur les mois où les ruptures de stocks ont eu un effet (le mois de la rupture et le mois suivant). <br/>

On sait en avance les refill de stocks qu'on aura. <br/>
Donc, on peut améliorer nos prédictions de cette façon:

$$ pred\_processed(item_i, month_M) = \min(stock(item_i, month_M), pred(item_i, month_M)) $$

8) Ajouter les objectifs des commerciaux.

Re-activer le test en renommant `def tst_model_with_objectives` -> `def test_model_with_objectives`

Les commerciaux ont des objectifs de vente à l'année. L'année fiscal se terminant en juin, c'est ce mois, et le mois suivant, qui sont impactés. <br/>
Si l'item a déjà fait son objectif, où est loin de le faire (resterait 20% des ventes à faire), il n'y a pas d'impact. <br/>
Sinon, l'équipe commercial va faire tout son possible pour arriver à l'objectif, demandant à leurs clients de sur-acheter en juin. Du coup, il y a un sous-achat en juillet compensant la sur-vente de juin.

Intégrer les données des objectifs à votre pipeline de prédiction.

9) Faire un modèle custom

Re-activer le test en renommant `def tst_custom_model` -> `def test_custom_model`

La génération des données a été faite ainsi. J'ai généré des données autoregressées ainsi:

$$sales\_v1(M) = a * sales(M-12) + b * sales(M-1:M-12) / 12 + c * sales(M-12) \frac{sales(M-1:M-3)}{sales(M-13:M-15)}$$

Ca fait, j'ai rajouté les effets:

$$ sales\_v2(M)  = sales\_v1(M) * (1 + d * marketing ) * (1 + e * price\_change) $$

J'ai ensuite ajouté, au hasard sur certains mois, des contraintes "objectifs commerciaux", puis des contraintes de stock.

Vous pouvez faire votre propre modèle qui reprend ces équations, avec les paramètres a, b, c....,e, et utilser scipy.optimize pour trouver les paramètres idéaux.

### Après 30 minutes

Les tests "test_model_prev_month" & "test_model_same_month_last_year"
**-1 point si non fait après 30 minutes**<br/>
**0 au TD si non fait après 1 heure**

### Après 1 heure

Vous avez fait l'auto-regressive model.<br/>
Le test "test_autoregressive_model" passe. <br/>
**-1 point si non fait après 1 heure**

## A rendre

Votre code src/.
