#!/usr/bin/env python

#
# Copyright 2024 Autodesk
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import fixturesUtils
import mayaUtils
import mayaUsd

from maya import cmds
from maya import standalone
from maya.internal.ufeSupport import ufeCmdWrapper as ufeCmd

import ufe
import unittest

class MetadataTestCase(unittest.TestCase):
    '''
    Verify the metadata functions.
    '''

    pluginsLoaded = False

    @classmethod
    def setUpClass(cls):
        fixturesUtils.readOnlySetUpClass(__file__, loadPlugin=False)

        if not cls.pluginsLoaded:
            cls.pluginsLoaded = mayaUtils.isMayaUsdPluginLoaded()

    @classmethod
    def tearDownClass(cls):
        standalone.uninitialize()

    def setUp(self):
        cmds.file(new=True, force=True)

    def runUndoRedo(self, capsuleItem, newVal, decimalPlaces=None):
        oldVal = capsuleItem.get()
        assert oldVal != newVal, "Undo / redo testing requires setting a value different from the current value"

        ufeCmd.execute(capsuleItem.setCmd(newVal))

        if decimalPlaces is not None:
            self.assertAlmostEqual(capsuleItem.get(), newVal, decimalPlaces)
            newVal = capsuleItem.get()
        else:
            self.assertEqual(capsuleItem.get(), newVal)

        cmds.undo()
        self.assertEqual(capsuleItem.get(), oldVal)
        cmds.redo()
        self.assertEqual(capsuleItem.get(), newVal)

    def testMetadata(self):
        '''Test prim metadata.'''
        # Create a capsule.
        import mayaUsd_createStageWithNewLayer
        proxyShape = mayaUsd_createStageWithNewLayer.createStageWithNewLayer()
        proxyShapePath = ufe.PathString.path(proxyShape)
        proxyShapeItem = ufe.Hierarchy.createItem(proxyShapePath)
        proxyShapeContextOps = ufe.ContextOps.contextOps(proxyShapeItem)
        cmd = proxyShapeContextOps.doOpCmd(['Add New Prim', 'Capsule'])
        ufeCmd.execute(cmd)

        capsulePath = ufe.PathString.path('%s,/Capsule1' % proxyShape)
        capsuleItem = ufe.Hierarchy.createItem(capsulePath)

        # Test for non-existing metadata.
        self.assertEqual(capsuleItem.getMetadata('doesNotExist'), ufe.Value())

        metaName = 'something'

        # Set the metadata and make sure it changed
        origValue = 'original value'
        capsuleItem.setMetadata(metaName, origValue)
        self.assertEqual(str(capsuleItem.getMetadata(metaName)), origValue)

        # Change the metadata and make sure it changed
        newValue = 'new value'
        capsuleItem.setMetadata(metaName, newValue)
        self.assertEqual(str(capsuleItem.getMetadata(metaName)), newValue)

        # Clear the metadata and make sure it is not equal to what we set it above.
        capsuleItem.clearMetadata(metaName)
        md = capsuleItem.getMetadata(metaName)
        self.assertEqual(capsuleItem.getMetadata(metaName), ufe.Value())

        def runMetadataUndoRedo(func, newValue, startValue=None):
            '''Helper to run metadata command on input value with undo/redo test.'''

            # Clear the metadata and make sure it is gone.
            if startValue:
                capsuleItem.setMetadata(metaName, startValue)
                self.assertFalse(capsuleItem.getMetadata(metaName).empty())
            else:
                capsuleItem.clearMetadata(metaName)
                self.assertEqual(capsuleItem.getMetadata(metaName), ufe.Value())

            # Set metadata using command.
            cmd = capsuleItem.setMetadataCmd(metaName, newValue)
            self.assertIsNotNone(cmd)
            cmd.execute()
            md = capsuleItem.getMetadata(metaName)
            self.assertEqual(md, ufe.Value(newValue))
            self.assertEqual(func(md), newValue)

            # Test undo/redo.
            cmd.undo()
            md = capsuleItem.getMetadata(metaName)
            if startValue:
                self.assertEqual(ufe.Value(startValue), md)
                self.assertEqual(startValue, func(md))
            else:
                self.assertEqual(capsuleItem.getMetadata(metaName), ufe.Value())
            cmd.redo()
            md = capsuleItem.getMetadata(metaName)
            self.assertEqual(ufe.Value(newValue), md)
            self.assertEqual(newValue, func(md))

        # Set the metadata using the command and verify undo/redo.
        # We test all the known ufe.Value types.
        # First with empty metadata and then with a starting metadata.
        runMetadataUndoRedo(bool, True)
        runMetadataUndoRedo(int, 10)
        runMetadataUndoRedo(float, 65.78)
        runMetadataUndoRedo(str, 'New value command')

        runMetadataUndoRedo(bool, True, False)
        runMetadataUndoRedo(int, 10, 2)
        runMetadataUndoRedo(float, 65.78, 0.567)
        runMetadataUndoRedo(str, 'New value command', 'New starting value')

    def testGroupMetadata(self):
        '''Test prim group metadata.'''
        # Create a capsule.
        import mayaUsd_createStageWithNewLayer
        proxyShape = mayaUsd_createStageWithNewLayer.createStageWithNewLayer()
        proxyShapePath = ufe.PathString.path(proxyShape)
        proxyShapeItem = ufe.Hierarchy.createItem(proxyShapePath)
        proxyShapeContextOps = ufe.ContextOps.contextOps(proxyShapeItem)
        cmd = proxyShapeContextOps.doOpCmd(['Add New Prim', 'Capsule'])
        ufeCmd.execute(cmd)

        capsulePath = ufe.PathString.path('%s,/Capsule1' % proxyShape)
        capsuleItem = ufe.Hierarchy.createItem(capsulePath)

        groupName = 'this group'
        metaName = 'something'

        # Test for non-existing metadata.
        self.assertEqual(capsuleItem.getGroupMetadata(groupName, 'doesNotExist'), ufe.Value())

        # Set the metadata and make sure it changed
        origValue = 'original value'
        capsuleItem.setGroupMetadata(groupName, metaName, origValue)
        self.assertEqual(str(capsuleItem.getGroupMetadata(groupName, metaName)), origValue)

        # Change the metadata and make sure it changed
        newValue = 'new value'
        capsuleItem.setGroupMetadata(groupName, metaName, newValue)
        self.assertEqual(str(capsuleItem.getGroupMetadata(groupName, metaName)), newValue)

        # Clear the metadata and make sure it is not equal to what we set it above.
        capsuleItem.clearGroupMetadata(groupName, metaName)
        md = capsuleItem.getGroupMetadata(groupName, metaName)
        self.assertEqual(capsuleItem.getGroupMetadata(groupName, metaName), ufe.Value())

        def runMetadataUndoRedo(func, newValue, startValue=None):
            '''Helper to run metadata command on input value with undo/redo test.'''

            # Clear the metadata and make sure it is gone.
            if startValue:
                capsuleItem.setGroupMetadata(groupName, metaName, startValue)
                self.assertFalse(capsuleItem.getGroupMetadata(groupName, metaName).empty())
            else:
                capsuleItem.clearGroupMetadata(groupName, metaName)
                self.assertEqual(capsuleItem.getGroupMetadata(groupName, metaName), ufe.Value())

            # Set metadata using command.
            cmd = capsuleItem.setGroupMetadataCmd(groupName, metaName, newValue)
            self.assertIsNotNone(cmd)
            cmd.execute()
            md = capsuleItem.getGroupMetadata(groupName, metaName)
            self.assertEqual(md, ufe.Value(newValue))
            self.assertEqual(func(md), newValue)

            # Test undo/redo.
            cmd.undo()
            md = capsuleItem.getGroupMetadata(groupName, metaName)
            if startValue:
                self.assertEqual(ufe.Value(startValue), md)
                self.assertEqual(startValue, func(md))
            else:
                self.assertEqual(capsuleItem.getGroupMetadata(groupName, metaName), ufe.Value())
            cmd.redo()
            md = capsuleItem.getGroupMetadata(groupName, metaName)
            self.assertEqual(ufe.Value(newValue), md)
            self.assertEqual(newValue, func(md))

        # Set the metadata using the command and verify undo/redo.
        # We test all the known ufe.Value types.
        # First with empty metadata and then with a starting metadata.
        runMetadataUndoRedo(bool, True)
        runMetadataUndoRedo(int, 10)
        runMetadataUndoRedo(float, 65.78)
        runMetadataUndoRedo(str, 'New value command')

        runMetadataUndoRedo(bool, True, False)
        runMetadataUndoRedo(int, 10, 2)
        runMetadataUndoRedo(float, 65.78, 0.567)
        runMetadataUndoRedo(str, 'New value command', 'New starting value')

    def testAutodeskGroupMetadata(self):
        '''Test the that the SessionLayer-Autodesk group metadata is routed to the session layer.'''
        # Create a capsule.
        import mayaUsd_createStageWithNewLayer
        proxyShape = mayaUsd_createStageWithNewLayer.createStageWithNewLayer()
        stage = mayaUsd.lib.GetPrim(proxyShape).GetStage()
        proxyShapePath = ufe.PathString.path(proxyShape)
        proxyShapeItem = ufe.Hierarchy.createItem(proxyShapePath)
        proxyShapeContextOps = ufe.ContextOps.contextOps(proxyShapeItem)
        cmd = proxyShapeContextOps.doOpCmd(['Add New Prim', 'Capsule'])
        ufeCmd.execute(cmd)

        capsulePath = ufe.PathString.path('%s,/Capsule1' % proxyShape)
        capsuleItem = ufe.Hierarchy.createItem(capsulePath)

        self.assertEqual(len(stage.GetSessionLayer().rootPrims), 0)

        autodeskName = 'SessionLayer-Autodesk'
        groupName = 'a-group'
        metaName = 'something'

        # Set the metadata on a normal group and make sure it changed and the session is still empty
        origValue = 'original value'
        capsuleItem.setGroupMetadata(groupName, metaName, origValue)
        self.assertEqual(str(capsuleItem.getGroupMetadata(groupName, metaName)), origValue)
        self.assertEqual(len(stage.GetSessionLayer().rootPrims), 0)

        # Set the metadata on the SessionLayer-Autodesk group and make sure it changed and the session contains something
        origValue = 'private value'
        capsuleItem.setGroupMetadata(autodeskName, metaName, origValue)
        self.assertEqual(str(capsuleItem.getGroupMetadata(autodeskName, metaName)), origValue)
        self.assertEqual(len(stage.GetSessionLayer().rootPrims), 1)


    def testGroupMetadataMultiLayers(self):
        '''Test prim group metadata composition between multiple layers.'''
        # Create a capsule.
        import mayaUsd_createStageWithNewLayer
        proxyShape = mayaUsd_createStageWithNewLayer.createStageWithNewLayer()
        stage = mayaUsd.lib.GetPrim(proxyShape).GetStage()
        proxyShapePath = ufe.PathString.path(proxyShape)
        proxyShapeItem = ufe.Hierarchy.createItem(proxyShapePath)
        proxyShapeContextOps = ufe.ContextOps.contextOps(proxyShapeItem)
        cmd = proxyShapeContextOps.doOpCmd(['Add New Prim', 'Capsule'])
        ufeCmd.execute(cmd)

        capsulePath = ufe.PathString.path('%s,/Capsule1' % proxyShape)
        capsuleItem = ufe.Hierarchy.createItem(capsulePath)

        executedCmds = []
        undoneCmds = []
                
        def setValue(name, value):
            cmd = capsuleItem.setGroupMetadataCmd(groupName, name, value)
            cmd.execute()
            executedCmds.append(cmd)

        def clearValue(name):
            cmd = capsuleItem.clearGroupMetadataCmd(groupName, name)
            cmd.execute()
            executedCmds.append(cmd)

        def undoLastCmd():
            self.assertGreater(len(executedCmds), 0)
            undoneCmds.append(executedCmds.pop())
            undoneCmds[-1].undo()

        def redoLastCmd():
            self.assertGreater(len(undoneCmds), 0)
            executedCmds.append(undoneCmds.pop())
            executedCmds[-1].redo()

        def verifyValue(name, expectedValue):
            expectedType = type(expectedValue)
            actualValue = capsuleItem.getGroupMetadata(groupName, name)
            actualType = type(actualValue)
            try:
                self.assertEqual(expectedType(actualValue), expectedValue,
                                'Expected %s value %s(%s), got %s(%s)' %
                                (name, expectedType, expectedValue, actualType, actualValue))
            except Exception:
                self.fail(
                    'Expected %s value %s(%s), got %s(%s)' %
                    (name, expectedType, expectedValue, actualType, actualValue))
                
        def verifyLayer(layer, expectedContents=None, rejectedContents=None):
            actualContents = layer.ExportToString()
            if expectedContents:
                for ec in expectedContents:
                    self.assertIn(ec, actualContents)
            if rejectedContents:
                for rc in rejectedContents:
                    self.assertNotIn(rc, actualContents)

        # Data used in test.
        groupName = 'this group'
        sessionMetaName = 'in-session'
        sessionValue = 5.1
        rootMetaName = 'in-root'
        rootValue = 33
        modifiedRootValue = 'changed-to-string'

        # Test for non-existing metadata.
        self.assertEqual(capsuleItem.getGroupMetadata(groupName, sessionMetaName), ufe.Value())
        self.assertEqual(capsuleItem.getGroupMetadata(groupName, rootMetaName), ufe.Value())
        verifyLayer(stage.GetSessionLayer(), rejectedContents=[sessionMetaName, rootMetaName])
        verifyLayer(stage.GetRootLayer(), rejectedContents=[sessionMetaName, rootMetaName])

        # Set metadata in the session layer and verify it changed
        stage.SetEditTarget(stage.GetSessionLayer())
        setValue(sessionMetaName, sessionValue)
        verifyValue(sessionMetaName, sessionValue)
        verifyLayer(stage.GetSessionLayer(), expectedContents=[sessionMetaName], rejectedContents=[rootMetaName])
        verifyLayer(stage.GetRootLayer(), rejectedContents=[sessionMetaName, rootMetaName])

        # Set metadata in the root layer and verify it changed
        stage.SetEditTarget(stage.GetRootLayer())
        setValue(rootMetaName, rootValue)
        verifyValue(rootMetaName, rootValue)
        verifyLayer(stage.GetSessionLayer(), expectedContents=[sessionMetaName], rejectedContents=[rootMetaName])
        verifyLayer(stage.GetRootLayer(), expectedContents=[rootMetaName], rejectedContents=[sessionMetaName])

        # Verify the session metadata is still accessible.
        verifyValue(sessionMetaName, sessionValue)

        # Set the root metadata in the session layer and verify it changed
        stage.SetEditTarget(stage.GetSessionLayer())
        setValue(rootMetaName, modifiedRootValue)
        verifyValue( rootMetaName, modifiedRootValue)
        verifyValue(sessionMetaName, sessionValue)
        verifyLayer(stage.GetSessionLayer(), expectedContents=[sessionMetaName, rootMetaName])
        verifyLayer(stage.GetRootLayer(), expectedContents=[rootMetaName], rejectedContents=[sessionMetaName])

        # Undo of setting root-in-session and verify the old root value is back.
        undoLastCmd()
        verifyValue(sessionMetaName, sessionValue)
        verifyValue(rootMetaName, rootValue)
        verifyLayer(stage.GetSessionLayer(), expectedContents=[sessionMetaName], rejectedContents=[rootMetaName])
        verifyLayer(stage.GetRootLayer(), expectedContents=[rootMetaName], rejectedContents=[sessionMetaName])

        # Redo of setting root-in-session and verify the bew root value is restored.
        redoLastCmd()
        verifyValue(sessionMetaName, sessionValue)
        verifyValue(rootMetaName, modifiedRootValue)
        verifyLayer(stage.GetSessionLayer(), expectedContents=[sessionMetaName, rootMetaName])
        verifyLayer(stage.GetRootLayer(), expectedContents=[rootMetaName], rejectedContents=[sessionMetaName])

        # Undo again so that there is only one value in teh session layer.
        undoLastCmd()
        verifyValue(sessionMetaName, sessionValue)
        verifyValue(rootMetaName, rootValue)
        verifyLayer(stage.GetSessionLayer(), expectedContents=[sessionMetaName], rejectedContents=[rootMetaName])
        verifyLayer(stage.GetRootLayer(), expectedContents=[rootMetaName], rejectedContents=[sessionMetaName])

        # Clear the session value, verify the root value is not in the session layer
        clearValue(sessionMetaName)
        verifyValue(sessionMetaName, ufe.Value())
        verifyValue(rootMetaName, rootValue)
        verifyLayer(stage.GetSessionLayer(), rejectedContents=[sessionMetaName, rootMetaName])
        verifyLayer(stage.GetRootLayer(), expectedContents=[rootMetaName], rejectedContents=[sessionMetaName])

        # Undo the clear value and verify there is a value in the session layer.
        undoLastCmd()
        verifyValue(sessionMetaName, sessionValue)
        verifyValue(rootMetaName, rootValue)
        verifyLayer(stage.GetSessionLayer(), expectedContents=[sessionMetaName], rejectedContents=[rootMetaName])
        verifyLayer(stage.GetRootLayer(), expectedContents=[rootMetaName], rejectedContents=[sessionMetaName])


if __name__ == '__main__':
    unittest.main(verbosity=2)
