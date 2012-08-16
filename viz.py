import handler


class SunburstHandler(handler.Handler):
    def get(self, profile_name):
        self.render('sunburst.html', profile_name=profile_name)
