import React from 'react'
import { Routes, Route } from 'react-router-dom'
import BrowseLevels from './BrowseLevels'
import BrowseStreams from './BrowseStreams'
import BrowseBoards from './BrowseBoards'
import ViewQuestions from './ViewQuestions'

export default function BrowsePage() {
  return (
    <Routes>
      <Route index element={<BrowseLevels />} />
      <Route path="level/:levelId" element={<BrowseStreams />} />
      <Route path="stream/:streamId" element={<BrowseBoards />} />
      <Route path="board/:boardId/:questionType" element={<ViewQuestions />} />
    </Routes>
  )
}