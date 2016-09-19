#!/bin/python

from antlr4 import *
from antlr4.tree.Trees import Trees
from codesensor2python.build.ModuleLexer import ModuleLexer
from codesensor2python.build.ModuleListener import ModuleListener
from codesensor2python.build.ModuleParser import ModuleParser
from parseutility import function, abstract

import sys


class TreeParser(ModuleListener):
	IS_FIRST = 1
	FUNCTION_DEF = 0
	FUNCTION_NAME = 1
	PARAMETER_NAME = 2
	DECLARATOR = 3
	TYPE_NAME = 4
	FUNCTION_CALL = 5
	
	table = ["function_def", "function_name", "parameter_name", "declarator", "type_name", "identifier"]
	IDX = [0, 0, 0, 0, 0, 0]
	
	def __init__(self):
		self.functionInstanceList = []
		
		# Function's name
		self.funcNameFlag = 0
		self.funcNameStr = ""
		
		# Function parameter's name
		self.paramNameFlag = 0
		self.paramNameStr = ""
		
		# Local variable's name
		self.declaratorFlag = 0
		self.declaratorStr = ""
		
		# type (return type, parameter type, local variable type)
		self.typeNameFlag = 0
		self.typeNameStr = ""
		
		# function definition
		self.funcDefFlag = 0
		
		self.funcCallFlag = 0
		self.funcCallStr = ""

		self.srcFileName = ""
		self.numLines = 0 # ??
	
	def _init(self, parser):
		self.__init__()
		
		if TreeParser.IS_FIRST:
			for i, ruleName in enumerate(parser.ruleNames):
				for j, tableName in enumerate(TreeParser.table):
					if ruleName == tableName:
						TreeParser.IDX[j] = i
		TreeParser.IS_FIRST = 0
	
	
	def ParseFile(self, srcFileName):
		input = FileStream(srcFileName)
		lexer = ModuleLexer(input)
		stream = CommonTokenStream(lexer)
		parser = ModuleParser(stream)
		tree = parser.code()
		self._init(parser)
		
		fp = open(srcFileName, 'r')
		srcFileRaw = fp.readlines()
		fp.close()
		self.numLines = len(srcFileRaw) #???
		self.srcFileName = srcFileName
		
		ParseTreeWalker().walk(self, tree)
		
		return self.functionInstanceList
	
	
	def enterEveryRule(self, ctx):
		ruleIndex = ctx.getRuleIndex()

		if ruleIndex == TreeParser.IDX[TreeParser.FUNCTION_DEF]:
			self.funcDefFlag = 1
			self.functionInstance = function(self.srcFileName)
			#self.functionInstanceList.append(self.functionInstance)
			self.functionInstance.parentNumLoc = self.numLines #????
			self.functionInstance.funcId = len(self.functionInstanceList)
			self.functionInstance.lines = (ctx.start.line, ctx.stop.line)
		
		elif ruleIndex == TreeParser.IDX[TreeParser.FUNCTION_NAME]:
			self.funcNameFlag = 1
		
		elif ruleIndex == TreeParser.IDX[TreeParser.PARAMETER_NAME]:
			self.paramNameFlag = 1
		
		elif ruleIndex == TreeParser.IDX[TreeParser.DECLARATOR]:
			self.declaratorFlag = 1
		
		elif ruleIndex == TreeParser.IDX[TreeParser.TYPE_NAME]:
			self.typeNameFlag = 1

		elif ruleIndex == TreeParser.IDX[TreeParser.FUNCTION_CALL]:
			self.funcCallFlag = 1
	
	
	def exitEveryRule(self, ctx):
		ruleIndex = ctx.getRuleIndex()

		if ruleIndex == TreeParser.IDX[TreeParser.FUNCTION_DEF] and self.funcDefFlag:
			self.funcDefFlag = 0
			self.functionInstanceList.append(self.functionInstance)
		elif ruleIndex == TreeParser.IDX[TreeParser.FUNCTION_NAME] and self.funcNameFlag:
			self.functionInstance.name = self.funcNameStr.rstrip()
			self.funcNameFlag = 0
			self.funcNameStr = ""
		elif ruleIndex == TreeParser.IDX[TreeParser.PARAMETER_NAME] and self.paramNameFlag:
			self.functionInstance.parameterList.append(self.paramNameStr.rstrip())
			self.paramNameFlag = 0
			self.paramNameStr = ""
		elif ruleIndex == TreeParser.IDX[TreeParser.DECLARATOR] and self.declaratorFlag:
			self.functionInstance.variableList.append(self.declaratorStr.rstrip())
			self.declaratorFlag = 0
			self.declaratorStr = ""
		elif ruleIndex == TreeParser.IDX[TreeParser.TYPE_NAME] and self.typeNameFlag:
			self.functionInstance.dataTypeList.append(self.typeNameStr.rstrip())
			self.typeNameFlag = 0
			self.typeNameStr = ""
		elif ruleIndex == TreeParser.IDX[TreeParser.FUNCTION_CALL] and self.funcCallFlag:
			self.functionInstance.funcCalleeList.append(self.funcCallStr.rstrip())
			self.funcCallFlag = 0
			self.funcCallStr = ""
	
	def visitTerminal(self, node):
		# print "node:", node
		if self.funcNameFlag:
			# print "FuncName", Trees.getNodeText(node)
			self.funcNameStr += (Trees.getNodeText(node) + ' ')
		
		elif self.paramNameFlag:
			# print "Parameter", Trees.getNodeText(node)
			self.paramNameStr += (Trees.getNodeText(node) + ' ')
		
		elif self.declaratorFlag:
			tmpText = Trees.getNodeText(node)
			# print "LvarName", Trees.getNodeText(node)

			if tmpText != "*": # remove pointer(*) in name of local variables
				self.declaratorStr += (tmpText + ' ')
		
		elif self.typeNameFlag:
			# print "TypeName", Trees.getNodeText(node)
			self.typeNameStr += (Trees.getNodeText(node) + ' ')

		elif self.funcCallFlag:
			print "self", node
			parentNodes = node.getParent()
			p1 = parentNodes
			p2 = p1.parentCtx
			p3 = p2.parentCtx
			p4 = p3.parentCtx

			print "p1", type(p1)
			print "p2", type(p2)
			print "p3", type(p3)
			print "p4", type(p4)
			print ""


			# print "\n\n\n"

			if str(type(p4)).endswith("FuncCallContext'>"):
				self.funcCallStr += (Trees.getNodeText(node) + ' ')
			# print type(parentNodes)
			# print parentNodes

			# parentNodesAsList = str(parentNodes)[1:-1].split(" ")
			# if len(parentNodesAsList) > 2:
			# 	if parentNodesAsList[2] == "50":

			# 		print "CALL", Trees.getNodeText(node)



def main(argv):
	functionInstanceList = TreeParser().ParseFile(argv[1])
	print argv[1]

	sys.exit()
	for f in functionInstanceList:
		f.removeListDup()
		print f.name, f.lines
		print "PARAMS\t", f.parameterList
		print "LVARS\t", f.variableList
		print "DTYPE\t", f.dataTypeList
		print "CALLS\t", f.funcCalleeList
		print ""

		for call in f.funcCalleeList:
			print call


		abstract(f, 4)

	sys.exit()

if __name__ == "__main__":
	main(sys.argv)
