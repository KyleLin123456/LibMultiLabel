from sklearn.base import BaseEstimator
from sklearn.utils.multiclass import unique_labels
from sklearn.utils.validation import check_is_fitted

import libmultilabel.linear as linear
from linear_trainer import linear_train


class MultiLabelMixin:
    """Mixin class for all classifiers in scikit-learn."""

    _estimator_type = "classifier"

    def __init__(self, metric_threshold=0, val_metric="P@1"):
        self.metrics = None
        self.metric_threshold = metric_threshold
        self.val_metric = val_metric

    def score(self, X, y):
        if self.metrics is None:
            self.metrics = linear.get_metrics(
                self.metric_threshold,
                [self.val_metric],
                y.shape[1],
            )
        preds = self.predict(X)
        target = y.toarray()
        self.metrics.update(preds, target)
        metric_dict = self.metrics.compute()
        return metric_dict[self.val_metric]

    def _more_tags(self):
        return {"requires_y": True}


class MultiLabelClassifier(MultiLabelMixin, BaseEstimator):
    def __init__(self, options, metric_threshold=0, val_metric="P@1", linear_technique="1vsrest"):
        super().__init__(metric_threshold, val_metric)
        self.options = options
        # Can we reuse this? (linear_trainer.linear_train)
        self.techniques = {
            '1vsrest': linear.train_1vsrest,
            'thresholding': linear.train_thresholding,
            'cost_sensitive': linear.train_cost_sensitive,
            'cost_sensitive_micro': linear.train_cost_sensitive_micro,
            'binary_and_multiclass': linear.train_binary_and_multiclass
        }
        self.linear_technique = linear_technique

    def fit(self, X, y):
        # Store the classes seen during fit
        self.classes_ = unique_labels(y)
        self.model = self.techniques[self.linear_technique](y, X, self.options)
        return self

    def predict(self, X):
        # Check if fit has been called
        check_is_fitted(self)
        preds = linear.predict_values(self.model, X)
        return preds
