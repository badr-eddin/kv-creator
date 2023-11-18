import os.path

from PyQt6.Qsci import *


class _AVS(QsciLexerAVS):
    def __init__(self, color, parent=None):
        super(_AVS, self).__init__(parent)
        self.setColor(color("Comment"), self.BlockComment)
        self.setColor(color("c7"), self.ClipProperty)
        self.setColor(color("c4"), self.Filter)
        self.setColor(color("c5"), self.Function)
        self.setColor(color("c1"), self.Keyword)
        self.setColor(color("c2"), self.KeywordSet6)
        self.setColor(color("Comment"), self.LineComment)
        self.setColor(color("Comment"), self.NestedBlockComment)
        self.setColor(color("c3"), self.Number)
        self.setColor(color("c6"), self.Operator)
        self.setColor(color("c5"), self.Plugin)
        self.setColor(color("c4"), self.String)
        self.setColor(color("c5"), self.TripleString)


class _Bash(QsciLexerBash):
    def __init__(self, color, parent=None):
        super(_Bash, self).__init__(parent)
        self.setColor(color("Backticks"), self.Backticks)
        self.setColor(color("Comment"), self.Comment)
        self.setColor(color("error"), self.Error)
        self.setColor(color("c4"), self.DoubleQuotedString)
        self.setColor(color("c3"), self.HereDocumentDelimiter)
        self.setColor(color("Foreground"), self.Identifier)
        self.setColor(color("c1"), self.Keyword)
        self.setColor(color("c5"), self.Number)
        self.setColor(color("c6"), self.Operator)
        self.setColor(color("c7"), self.ParameterExpansion)
        self.setColor(color("c2"), self.Scalar)
        self.setColor(color("c4"), self.SingleQuotedHereDocument)
        self.setColor(color("c4"), self.SingleQuotedString)


class _Batch(QsciLexerBatch):
    def __init__(self, color, parent=None):
        super(_Batch, self).__init__(parent)
        self.setColor(color("Foreground"), self.Default)
        self.setColor(color("Comment"), self.Comment)
        self.setColor(color("c1"), self.Keyword)
        self.setColor(color("c5"), self.ExternalCommand)
        self.setColor(color("c4"), self.HideCommandChar)
        self.setColor(color("c2"), self.Label)
        self.setPaper(color("Transparent"), self.Label)
        self.setColor(color("c6"), self.Operator)
        self.setColor(color("c7"), self.Variable)


class _CMake(QsciLexerCMake):
    def __init__(self, color, parent=None):
        super(_CMake, self).__init__(parent)
        self.setColor(color("Foreground"), self.Default)
        self.setColor(color("Comment"), self.Comment)
        self.setColor(color("c4"), self.String)
        self.setColor(color("c5"), self.StringLeftQuote)
        self.setColor(color("c5"), self.StringRightQuote)
        self.setColor(color("c3"), self.StringVariable)
        self.setColor(color("c1"), self.Function)
        self.setColor(color("c7"), self.Variable)
        self.setColor(color("c2"), self.Label)
        self.setColor(color("c6"), self.KeywordSet3)
        self.setColor(color("c4"), self.BlockForeach)
        self.setColor(color("c4"), self.BlockIf)
        self.setColor(color("c4"), self.BlockMacro)
        self.setColor(color("c4"), self.BlockWhile)
        self.setColor(color("c3"), self.Number)


class _CoffeeScript(QsciLexerCoffeeScript):
    def __init__(self, color, parent=None):
        super(_CoffeeScript, self).__init__(parent)
        self.setColor(color("Comment"), self.Comment)
        self.setColor(color("Comment"), self.CommentBlock)
        self.setColor(color("Comment"), self.CommentDoc)
        self.setColor(color("Comment"), self.CommentLine)
        self.setColor(color("Comment"), self.CommentLineDoc)
        self.setColor(color("c4"), self.DoubleQuotedString)
        self.setColor(color("c1"), self.Keyword)
        self.setColor(color("c6"), self.KeywordSet2)
        self.setColor(color("c3"), self.Number)
        self.setColor(color("c6"), self.Operator)
        self.setColor(color("c7"), self.UUID)
        self.setColor(color("error"), self.UnclosedString)
        self.setColor(color("c4"), self.SingleQuotedString)
        self.setColor(color("c5"), self.VerbatimString)
        self.setColor(color("c2"), self.Regex)
        self.setColor(color("Comment"), self.BlockRegex)
        self.setColor(color("Comment"), self.BlockRegexComment)
        self.setColor(color("Foreground"), self.Identifier)
        self.setColor(color("c6"), self.GlobalClass)
        self.setColor(color("c4"), self.InstanceProperty)


class _JSON(QsciLexerJSON):
    def __init__(self, color, parent=None):
        super(_JSON, self).__init__(parent)
        self.setColor(color("Comment"), self.CommentBlock)
        self.setColor(color("Comment"), self.CommentLine)
        self.setColor(color("Foreground"), self.Default)
        self.setColor(color("Error"), self.Error)
        self.setColor(color("c1"), self.EscapeSequence)
        self.setColor(color("Foreground"), self.IRI)
        self.setColor(color("Foreground"), self.IRICompact)
        self.setColor(color("c1"), self.Keyword)
        self.setColor(color("c1"), self.KeywordLD)
        self.setColor(color("c7"), self.Number)
        self.setColor(color("c6"), self.Operator)
        self.setColor(color("c4"), self.Property)
        self.setColor(color("c3"), self.String)
        self.setColor(color("Error"), self.UnclosedString)


class _Properties(QsciLexerProperties):
    def __init__(self, color, parent=None):
        super(_Properties, self).__init__(parent)
        self.setColor(color("Comment"), self.Assignment)
        self.setColor(color("Comment"), self.Comment)
        self.setColor(color("Foreground"), self.Default)
        self.setColor(color("c5"), self.DefaultValue)
        self.setColor(color("c1"), self.Key)
        self.setColor(color("c7"), self.Section)


class _CPP(QsciLexerCPP): pass


class _CSharp(QsciLexerCSharp): pass


class _CSS(QsciLexerCSS): pass


class _D(QsciLexerD): pass


class _Diff(QsciLexerDiff): pass


class _Fortran(QsciLexerFortran): pass


class _HTML(QsciLexerHTML): pass


class _Java(QsciLexerJava): pass


class _JavaScript(QsciLexerJavaScript): pass


class _Lua(QsciLexerLua): pass


class _Makefile(QsciLexerMakefile): pass


class _Markdown(QsciLexerMarkdown): pass


class _Matlab(QsciLexerMatlab): pass


class _Octave(QsciLexerOctave): pass


class _Pascal(QsciLexerPascal): pass


class _Perl(QsciLexerPerl): pass


class _PO(QsciLexerPO): pass


class _PostScript(QsciLexerPostScript): pass


class _POV(QsciLexerPOV): pass


class _Ruby(QsciLexerRuby): pass


class _Spice(QsciLexerSpice): pass


class _SQL(QsciLexerSQL): pass


class _TCL(QsciLexerTCL): pass


class _TeX(QsciLexerTeX): pass


class _Verilog(QsciLexerVerilog): pass


class _VHDL(QsciLexerVHDL): pass


class _XML(QsciLexerXML): pass


class _YAML(QsciLexerYAML): pass


# when you have done all the lexers use re.match and ask chatgpt to write extensions instead
_LEXERS = {
    ".avs": _AVS,
    ".sh": _Bash,
    ".bat": _Batch,
    ".cmk": _CMake,
    ".coffee": _CoffeeScript,
    ".json": _JSON,
    ".properties": _Properties
}


class SuperLexer:
    FUNCTIONS = ["on_lexer_setup_done"]

    @staticmethod
    def on_lexer_setup_done(args):
        if not args.get("path") or not args.get("color"):
            return

        lexer = _LEXERS.get(os.path.splitext(args.get("path"))[1])

        if not lexer:
            return

        lexer = lexer(args.get("color"))
        return lexer


CLASS = SuperLexer
VERSION = 0.1
TYPE = "editors/function"
NAME = "super"
