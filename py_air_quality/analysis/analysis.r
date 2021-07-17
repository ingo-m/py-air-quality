# WORK IN PROGRESS

# https://www.rdocumentation.org/packages/nlme/versions/3.1-152/topics/gls

library(nlme)

# Read CSV into R
df <- read.csv(file='/home/john/PhD/GitHub/py-air-quality/py_air_quality/data/preprocessed.csv', header=TRUE, sep=';')

head(df)

# model = lm(pm25_internal ~ filter + pm25_external,
#            data=df)
# summary(model)

# form=(~1|timestamp)

model = gls(pm25_internal ~ filter + pm25_external,
            data=df,
            correlation=corCAR1(form=(~timestamp)),
            verbose=TRUE)

summary(model)
