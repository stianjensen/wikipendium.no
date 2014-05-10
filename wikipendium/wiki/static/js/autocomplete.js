(function($) {
  $.fn.autocomplete = function(articles) {
    return this.each(function() {

      var sb = $(this).focus();
      var ul = $('#suggestions');
      var ullength = articles.length;
      var oldword = "";
      var index = 0;

      ul.on('mouseover', 'li', function(e) {
        $(ul.children()[index]).removeClass("active");
        index = $(this).attr('data-idx') | 0;
        $(this).addClass("active");
      }).on('mouseout', 'li', function(e) {
        if(!sb.val()) {
          $(this).removeClass('active');
        }
      });

      function search(articles, word){
        if (word.length == 0) return [];

        word = word.toLowerCase();
        var ret = [];
        for (var i=0;i<articles.length;i++) {
          if (articles[i].label.toLowerCase().indexOf(word) !== -1) {
            ret.push(articles[i]);
          }
        }

        function heuristic(element) {
          return element.label.toLowerCase().split(' ').map(
              function (substring) {
                return substring.indexOf(word);
              }
              ).reduce(function(a, b) {
            return a + b;
          }, 0) + element.label.toLowerCase().indexOf(word);
        }

        ret.sort(function(a, b) {
          return heuristic(a) - heuristic(b);
        });

        return ret;
      }

      function render(articles) {
        ul.empty();
        for (var i=0;i<articles.length;i++) {
          var li = document.createElement("li");
          li.setAttribute('data-idx', i);

          var a = document.createElement("a");
          a.setAttribute('href', articles[i].url);
          a.textContent = articles[i].label;

          var date = document.createElement("p");
          date.textContent = "Last updated: " +
              moment(articles[i].updated).fromNow() + ".";
          date.setAttribute('class', 'date');

          a.appendChild(date);
          li.appendChild(a);
          ul.append(li); 
        }

        if (sb.val()) {
          $(ul.children()[index]).addClass("active");
        }

        if (ul.children().length == 0) {
          ullength = 0;
          var li = document.createElement("li");
          li.textContent = "Sorry no compendiums were found";
          li.setAttribute('class', 'no-found');
          ul.append(li);
        }
      }


      $("body").on("keydown", function(e) {
        if (!sb.val()) return;
        if (e.keyCode == 13) { //enter
          e.preventDefault();
          var url = $(ul.children()[index]).children('a').attr('href') || escape(sb.val());
          window.location = url;
        }
        if (e.keyCode == 38) { //up
          e.preventDefault();
          index = (index-1)%ullength;
        } else if (e.keyCode == 40) { //down
          e.preventDefault();
          index = (index+1)%ullength;
        } else {
          return;
        }
        ul.children().removeClass('active');
        $(ul.children()[index]).addClass("active");
      });

      render(articles);

      var refresh = function(e) {
        if (oldword === sb.val()) return;
        oldword = sb.val();
        index = 0;
        var words = search(articles, oldword);
        if (sb.val()) {
          ullength = words.length;
          render(words);
        } else {
          ullength = articles.length;
          render(articles);
        }
      }

      setInterval(refresh,100);
    });
  };
})(jQuery);
