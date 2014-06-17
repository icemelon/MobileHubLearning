## MobileHub Learning

### File Description
1. (user)\_(activity)\_(length).csv

        sensor trace file

2. (app)\_(user)\_(activity).log

        app behavior log (after which sensor data, the app updates)

3. (app)\_(user)\_(activity).csv

        sensor trace file with labels (trigger events or not)

4. (app)\_(user)\_(activity).gap

        #(sensor data) between two events --> window size = median number

5. (app)\_(user)\_(activity).buffer

        buffer trace: it provides every buffer sizes and sensor data as follow

### Command
- `data.py [sensor data(#1)] [taint log(#2)]`

        output
        - sensor trace with labels (file #3)
        - gap file (file #4)
        - window size

- `feature.py [label trace(#3)] [window size] [train/test]`
    
        output
        - training.arff/testing.arff (training/testing data used by Weka)

- `classify.py [window size]`

        requires training.arff and testing.arff in the same folder
        output
        - prediction results with different parameters

- `predict.py [label trace(#3)] [prediction result]`

        (currently not well defined)
        output: buffer trace (file #5)
        
