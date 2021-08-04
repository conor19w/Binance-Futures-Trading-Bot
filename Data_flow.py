import pandas as pd
import numpy as np


########### Simulate flow of live data for testing indicators ############
def dataflow(dataStream,data,currentPriceIndex,largestSMAsize,SmallestSMAsize):
    ##window of data is largestSMA+smallestSMA+10
    slidingwindow=[]
    ## sliding window of data for more efficient code
    if len(dataStream)>=largestSMAsize+SmallestSMAsize: ## ensure data doesnt grow too large
       for i in range(currentPriceIndex-largestSMAsize-SmallestSMAsize,currentPriceIndex+1):
           slidingwindow.append(data[i])
       return slidingwindow
    ##Add in next data point
    else:
        dataStream.append(data[len(dataStream)])
    ##return appended data
    return dataStream

def flowLive(data,length):
    slidingwindow = []
    for i in range(len(data) - length-1, len(data)-1):
        slidingwindow.append(data[i])
    return slidingwindow

def dataStream(data,newdata,type,length):
    if type==0:
        if len(data)<300:
            data.append(newdata)
            return data
        else:
            slidingwindow = []
            for i in range(len(data)-299,len(data)):
                slidingwindow.append(data[i])
            slidingwindow.append(newdata)
            return slidingwindow
    elif type==1:
        if len(data)<length:
            data.append(newdata)
            return data
        else:
            slidingwindow = []
            for i in range(len(data)-length+1,len(data)):
                slidingwindow.append(data[i])
            slidingwindow.append(newdata)
            return slidingwindow
    else:
        if len(data)<length:
            data.append(newdata)
            return data
        else:
            slidingwindow = []
            for i in range(len(data)-length+1,len(data)):
                slidingwindow.append(data[i])
            slidingwindow.append(newdata)
            return slidingwindow