R model:
```
model = gls(pm25_internal ~ filter + pm25_external,
            data=df,
            correlation=corCAR1(form=(~timestamp)),
            verbose=TRUE)

summary(model)
```

Result:
```
Generalized least squares fit by REML
  Model: pm25_internal ~ filter + pm25_external 
  Data: df 
       AIC      BIC    logLik
  6297.616 6325.919 -3143.808

Correlation Structure: Continuous AR(1)
 Formula: ~timestamp 
 Parameter estimate(s):
Phi 
0.2 

Coefficients:
                   Value  Std.Error   t-value p-value
(Intercept)    1.5837490 0.07528649  21.03630       0
filterTrue    -1.4584697 0.06360868 -22.92879       0
pm25_external  0.1262978 0.00471432  26.79024       0

 Correlation: 
              (Intr) fltrTr
filterTrue    -0.747       
pm25_external -0.631  0.055

Standardized residuals:
       Min         Q1        Med         Q3        Max 
-2.3319618 -0.4965809 -0.1730587  0.2768960 19.4516385 

Residual standard error: 1.057825 
Degrees of freedom: 2126 total; 2123 residual
```
