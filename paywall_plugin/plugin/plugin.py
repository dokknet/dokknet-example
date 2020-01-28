"""Mkdocs plugin to generate paywall pages for your documentation.

Each documentation page will be duplicated with a /paywall prefix, where page
content is truncated and the user is notified that they need to log in to
continue.
"""
from pathlib import Path
import shutil
from tempfile import mkdtemp

from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import Files
from mkdocs.structure.nav import Navigation


_paywall_notice = """
<div class="admonition info">
    <p class="admonition-title">Dokknet Login Required</p> 
    <p>
        Please log in at 
        <a href="https://dokknet.com/login" target="_blank">
            https://dokknet.com/login
        </a>
        to view the rest of this page.
    </p>
    <p>No registration necessary, you just get a login link to your email and you can continue right away.</p>
</div>
"""


class PaywallPlugin(BasePlugin):
    config_scheme = (
        ('show_toggle_button', config_options.Type(bool, default=False)),
    )

    _tmp_prefix = 'mkdocs-paywall-plugin-'
    _paywall_dir = 'paywall'
    _supported_themes = {'material'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tmp dir will be used as source directory for the build
        self._tmp_dir = Path(mkdtemp(prefix=self._tmp_prefix))
        self._tmp_docs_dir = self._tmp_dir / 'docs'
        # The docs dir from the original configs
        self._docs_dir = None

    def _add_paywall_notice(self, html):
        return html + _paywall_notice

    def _is_paywall_file(self, file):
        return file.src_path.startswith(self._paywall_dir)

    def _is_paywall_page(self, page):
        return self._is_paywall_file(page.file)

    def _truncate_html(self, html):
        p_end = '</p>'
        first_p_end = html.find(p_end)
        if first_p_end > -1:
            html = html[:first_p_end + len(p_end)]
        return html

    def on_config(self, config, *args, **kwargs):
        print(config['theme'])
        theme = config['theme'].name
        if theme not in self._supported_themes:
            raise RuntimeError(f'Theme "{theme}" is not in supported themes: '
                               f'{self._supported_themes}')
        self._docs_dir = config['docs_dir']
        config['docs_dir'] = str(self._tmp_docs_dir)
        return config

    def on_page_content(self, html, page, *args, **kwargs):
        if self._is_paywall_page(page):
            pre_html = self._truncate_html(html)
            res = self._add_paywall_notice(pre_html)
        else:
            res = html
        return res

    def on_pre_build(self, *args, **kwargs):
        shutil.copytree(self._docs_dir, self._tmp_docs_dir)

        # Duplicate docs in paywall directory
        pw_dir = self._tmp_docs_dir / self._paywall_dir
        # TODO (abiro) what if doc dir has 'paywall' directory already
        shutil.copytree(self._docs_dir, pw_dir)

    def on_post_build(self,  *args, **kwargs):
        # TODO (abiro) this won't be invoked if there was an error in the build
        shutil.rmtree(self._tmp_dir)

    def on_files(self, files: Files, *args, **kwargs):
        # Make sure paywall pages have the same url as the original page
        doc_files = list(files.documentation_pages())
        for f in doc_files:
            if self._is_paywall_file(f):
                url = Path(f.url)
                f.url = str(url.relative_to(self._paywall_dir))
        return files

    def on_nav(self, nav, *args, **kwargs):
        # Remove paywall pages from nav
        pages = [p for p in nav.pages if not self._is_paywall_page(p)]
        items = []
        for item in nav.items:
            name = getattr(item, 'title', None)
            if name is None:
                name = item.file.src_path
            if not name.lower().startswith(self._paywall_dir):
                items.append(item)
        return Navigation(items, pages)

