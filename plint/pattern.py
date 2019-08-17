from plint import error


class Pattern:
    def __init__(self, metric, my_id="", feminine_id="", constraint=None, hemistiches=None):
        self.metric = metric
        self.length = None
        self.parse_metric()
        self.my_id = my_id
        self.feminine_id = feminine_id
        self.constraint = constraint
        if hemistiches:
            self.hemistiches = hemistiches

    def parse_metric(self):
        """Parse from a metric description"""
        try:
            verse = [int(x) for x in self.metric.split('/')]
            for i in verse:
                if i < 1:
                    raise ValueError
        except ValueError:
            raise error.TemplateLoadError("Metric description should only contain positive integers")
        if sum(verse) > 16:
            raise error.TemplateLoadError("Metric length limit exceeded")
        self.hemistiches = []
        self.length = 0
        for v in verse:
            self.length += v
            self.hemistiches.append(self.length)
        self.length = self.hemistiches.pop()
